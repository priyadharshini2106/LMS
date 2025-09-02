# hostel/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View
from .forms import RoomForm, BedFormSet
from django.db.models import Count, Q
from django.db.utils import ProgrammingError, OperationalError, DatabaseError
from django.contrib.messages.views import SuccessMessageMixin

from .models import HostelPayment
from .forms import PaymentForm
from django.views.decorators.http import require_POST
from django.views.generic import (
    ListView, CreateView, DetailView, TemplateView, UpdateView, DeleteView
)

from .models import (
    Hostel, Room, Bed, Allocation,
    HostelPayment, VisitorLog, Outpass, Complaint, OutpassHistory
)
from .forms import (
    HostelForm, AllocationForm, PaymentForm,
    VisitorForm, OutpassRequestForm, ComplaintForm, OutpassForm
)

from students.models import Student
from .models import Outpass
from .forms import OutpassRequestForm


# -------------------- Dashboard --------------------
class HostelDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hostel/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        def safe_count(qs_fn, default=0):
            try:
                return qs_fn().count()
            except (ProgrammingError, OperationalError, DatabaseError):
                # tables missing, db not migrated, or other db-level issue
                return default
            except Exception:
                # last-resort guard so dashboard never 500s
                return default

        ctx["total_hostels"]      = safe_count(lambda: Hostel.objects.all())
        ctx["alloc_active"]       = safe_count(lambda: Allocation.objects.filter(status="ACTIVE"))
        ctx["payments_total"]     = safe_count(lambda: HostelPayment.objects.all())
        ctx["complaints_open"]    = safe_count(lambda: Complaint.objects.filter(status__in=["OPEN", "IN_PROGRESS"]))
        ctx["outpasses_pending"]  = safe_count(lambda: Outpass.objects.filter(status="Pending"))
        return ctx
    
# -------------------- Hostels --------------------
class HostelListView(ListView):
    model = Hostel
    template_name = 'hostel/hostel_list.html'
    context_object_name = 'hostels'

    def get_queryset(self):
        try:
            qs = super().get_queryset()
            q = self.request.GET.get('q')
            if q:
                qs = qs.filter(name__icontains=q) | qs.filter(code__icontains=q) | qs.filter(warden_name__icontains=q)
            return qs
        except (ProgrammingError, OperationalError, DatabaseError):
            # Tables not ready yet → show empty list instead of 500
            from django.contrib import messages
            messages.warning(self.request, "Hostel tables are not migrated yet. Showing empty list.")
            return Hostel.objects.none()


class HostelCreateView(SuccessMessageMixin, CreateView):
    model = Hostel
    template_name = "hostel/hostel_form.html"
    fields = ["name","code","capacity","gender_policy","warden_name","warden_contact","warden_image"]
    success_url = reverse_lazy("hostel:hostel_list")
    success_message = "Hostel “%(name)s” was created successfully."


class HostelUpdateView(SuccessMessageMixin, UpdateView):
    model = Hostel
    template_name = "hostel/hostel_form.html"
    fields = ["name","code","capacity","gender_policy","warden_name","warden_contact","warden_image"]
    success_url = reverse_lazy("hostel:hostel_list")
    success_message = "Hostel “%(name)s” was updated successfully."


class HostelDeleteView(DeleteView):
    model = Hostel
    template_name = "hostel/confirm_delete.html"
    success_url = reverse_lazy("hostel:hostel_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Hostel “{obj.name}” was deleted.')
        return response
    
# ---------------- Rooms ----------------
# === Room List View ===
class RoomListView(ListView):
    model = Room
    template_name = "hostel/room_list.html"
    context_object_name = "rooms"
    paginate_by = 20  # Number of rooms per page

# === Room Create View ===
class RoomCreateView(CreateView):
    model = Room
    form_class = RoomForm
    template_name = "hostel/room_form.html"
    success_url = reverse_lazy("hostel:room_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["formset"] = BedFormSet(self.request.POST, instance=Room(), prefix="beds")
        else:
            context["formset"] = BedFormSet(instance=Room(), prefix="beds")
        return context

    def form_valid(self, form):
        # Save the room (parent form)
        self.object = form.save()
        # Rebuild the formset with the saved room instance and POST data
        formset = BedFormSet(self.request.POST, instance=self.object, prefix="beds")
        if formset.is_valid():
            formset.save()  # Save the beds
            return redirect(self.get_success_url())
        # If formset is invalid, show errors
        return render(self.request, self.template_name, {"form": form, "formset": formset})

# === Room Update View ===
class RoomUpdateView(UpdateView):
    model = Room
    form_class = RoomForm
    template_name = "hostel/room_form.html"
    success_url = reverse_lazy("hostel:room_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["formset"] = BedFormSet(self.request.POST, instance=self.object, prefix="beds")
        else:
            context["formset"] = BedFormSet(instance=self.object, prefix="beds")
        return context

    def form_valid(self, form):
        self.object = form.save()  # Save the Room instance
        formset = BedFormSet(self.request.POST, instance=self.object, prefix="beds")
        if formset.is_valid():
            formset.save()  # Save the beds
            return redirect(self.get_success_url())
        return render(self.request, self.template_name, {"form": form, "formset": formset})

# === Room Delete View ===
class RoomDeleteView(DeleteView):
    model = Room
    template_name = "hostel/room_confirm_delete.html"
    success_url = reverse_lazy("hostel:room_list")

# -------------------- Allocations --------------------
class AllocationListView(LoginRequiredMixin, ListView):
    model = Allocation
    template_name = 'hostel/allocation_list.html'
    context_object_name = 'allocations'
    queryset = Allocation.objects.select_related(
        "student", "bed", "bed__room", "bed__room__hostel"
    ).order_by("-date_allocated")


class AllocationCreateView(LoginRequiredMixin, CreateView):
    model = Allocation
    template_name = 'hostel/allocation_form.html'
    form_class = AllocationForm
    success_url = reverse_lazy('hostel:allocation_list')

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        bed = self.object.bed
        if bed.is_available:
            bed.is_available = False
            bed.save(update_fields=["is_available"])
        messages.success(self.request, "Allocation created")
        return response


class AllocationDetailView(LoginRequiredMixin, DetailView):
    model = Allocation
    template_name = 'hostel/allocation_detail.html'
    context_object_name = 'allocation'

class AllocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Allocation
    form_class = AllocationForm
    template_name = 'hostel/allocation_form.html'
    success_url = reverse_lazy('hostel:allocation_list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Allocation updated successfully.")
        return resp


class AllocationDeleteView(LoginRequiredMixin, DeleteView):
    model = Allocation
    template_name = 'hostel/confirm_delete.html'
    success_url = reverse_lazy('hostel:allocation_list')

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        bed = obj.bed
        response = super().delete(request, *args, **kwargs)
        if bed:
            bed.is_available = True
            bed.save(update_fields=["is_available"])
        messages.success(request, "Allocation deleted.")
        return response

# -------------------- Payments --------------------
# List all payments with search functionality
class PaymentListView(LoginRequiredMixin, ListView):
    model = HostelPayment
    template_name = "hostel/payment_list.html"
    context_object_name = "payments"
    ordering = ["-payment_date"]

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q', '')

        if search_query:
            queryset = queryset.filter(
                Q(student__name__icontains=search_query) |
                Q(hostel__name__icontains=search_query) |
                Q(amount__icontains=search_query) |
                Q(payment_date__icontains=search_query) |
                Q(method__icontains=search_query)
            )
        return queryset

# Create a new payment
class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = HostelPayment
    form_class = PaymentForm
    template_name = "hostel/payment_form.html"
    success_url = reverse_lazy("hostel:payment_list")

    def form_valid(self, form):
        messages.success(self.request, "✅ Payment recorded successfully.")
        return super().form_valid(form)

# Update an existing payment
class PaymentUpdateView(LoginRequiredMixin, UpdateView):
    model = HostelPayment
    form_class = PaymentForm
    template_name = "hostel/payment_form.html"
    success_url = reverse_lazy("hostel:payment_list")

    def form_valid(self, form):
        messages.success(self.request, "✏️ Payment updated successfully.")
        return super().form_valid(form)

# View details of a payment
class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = HostelPayment
    template_name = "hostel/payment_detail.html"
    context_object_name = "payment"

# Delete a payment
class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = HostelPayment
    template_name = "hostel/confirm_delete.html"
    success_url = reverse_lazy("hostel:payment_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "🗑️ Payment deleted successfully.")
        return super().delete(request, *args, **kwargs)
    

# -------------------- Visitors --------------------
class VisitorListView(LoginRequiredMixin, ListView):
    model = VisitorLog
    template_name = 'hostel/visitor_list.html'
    context_object_name = 'visitors'
    queryset = VisitorLog.objects.select_related("hostel").order_by("-visit_date", "-in_time")


class VisitorCreateView(LoginRequiredMixin, CreateView):
    model = VisitorLog
    form_class = VisitorForm
    template_name = 'hostel/visitor_form.html'
    success_url = reverse_lazy('hostel:visitor_list')

    def form_valid(self, form):
        # Optional: automatically track which user added the visitor
        # form.instance.added_by = self.request.user  # uncomment if field exists
        resp = super().form_valid(form)
        messages.success(self.request, "Visitor saved successfully!")
        return resp


class VisitorUpdateView(LoginRequiredMixin, UpdateView):
    model = VisitorLog
    form_class = VisitorForm
    template_name = 'hostel/visitor_form.html'
    success_url = reverse_lazy('hostel:visitor_list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Visitor updated successfully!")
        return resp


class VisitorDetailView(LoginRequiredMixin, DetailView):
    model = VisitorLog
    template_name = 'hostel/visitor_detail.html'
    context_object_name = 'visitor'

class VisitorDeleteView(LoginRequiredMixin, DeleteView):
    model = VisitorLog
    template_name = 'hostel/visitor_confirm_delete.html'  # optional, can use a simple confirmation
    success_url = reverse_lazy('hostel:visitor_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Visitor deleted successfully!")
        return super().delete(request, *args, **kwargs)


# -------------------- Outpasses (list/create/update/delete) --------------------

class OutpassListView(LoginRequiredMixin, ListView):
    model = Outpass
    template_name = 'hostel/outpass_list.html'
    context_object_name = 'outpasses'
    queryset = Outpass.objects.select_related("student").order_by("-start_date")  # Corrected to start_date


class OutpassCreateView(LoginRequiredMixin, CreateView):
    model = Outpass
    form_class = OutpassForm
    template_name = 'hostel/outpass_form.html'
    success_url = reverse_lazy('hostel:outpass_list')

    def form_valid(self, form):
        form.instance.status = "Pending"  # new requests start as pending
        resp = super().form_valid(form)
        messages.success(self.request, "Outpass created successfully")
        return resp


class OutpassUpdateView(LoginRequiredMixin, UpdateView):
    model = Outpass
    form_class = OutpassForm
    template_name = 'hostel/outpass_form.html'
    success_url = reverse_lazy('hostel:outpass_list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Outpass updated successfully")
        return resp


class OutpassDeleteView(LoginRequiredMixin, DeleteView):
    model = Outpass
    template_name = 'hostel/confirm_delete.html'
    success_url = reverse_lazy('hostel:outpass_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Outpass deleted successfully")
        return super().delete(request, *args, **kwargs)


# -------------------- Approve / Reject Actions --------------------
from django.views import View

class OutpassApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        outpass = get_object_or_404(Outpass, pk=pk)
        outpass.status = "Approved"
        outpass.save()
        messages.success(request, f"Outpass for {outpass.student} approved")
        return redirect('hostel:outpass_list')


class OutpassRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        outpass = get_object_or_404(Outpass, pk=pk)
        outpass.status = "Rejected"
        outpass.save()
        messages.success(request, f"Outpass for {outpass.student} rejected")
        return redirect('hostel:outpass_list')


# -------------------- Complaints --------------------
class ComplaintListView(LoginRequiredMixin, ListView):
    model = Complaint
    template_name = 'hostel/complaint_list.html'
    context_object_name = 'complaints'
    # Only student exists on Complaint; remove "hostel"
    queryset = Complaint.objects.select_related("student").order_by("-date_created")


class ComplaintCreateView(LoginRequiredMixin, CreateView):
    model = Complaint
    form_class = ComplaintForm
    template_name = 'hostel/complaint_form.html'
    success_url = reverse_lazy('hostel:complaint_list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Complaint submitted")
        return resp
    

# ------------- Student Search API -------------
def student_search(request):
    """
    1) ?q=partial -> list of {id, admission, name, class}
    2) ?admission_no=EXACT -> single {id, name, admission_number, class_name, section}
    """
    adm = (request.GET.get("admission_no") or "").strip()
    if adm:
        s = get_object_or_404(
            Student.objects.select_related("class_section"),
            admission_number__iexact=adm
        )
        class_name = getattr(s.class_section, "class_name", "") or ""
        section = getattr(s.class_section, "section", "") or ""
        return JsonResponse({
            "id": s.id,
            "name": s.name,
            "admission_number": s.admission_number,
            "class_name": class_name,
            "section": section,
        })

    term = (request.GET.get("q") or "").strip()
    data = []
    if term:
        qs = (
            Student.objects
            .select_related("class_section")
            .filter(Q(admission_number__icontains=term) | Q(name__icontains=term))
            .order_by("name")[:10]
        )
        for s in qs:
            class_name = getattr(s.class_section, "class_name", "") or ""
            section = getattr(s.class_section, "section", "") or ""
            label_cls = f"{class_name} - {section}".strip(" -")
            data.append({
                "id": s.id,
                "admission": s.admission_number,
                "name": s.name,
                "class": label_cls,
            })
    return JsonResponse(data, safe=False)

#---------OutPass---------------#
# List View for Outpasses
class OutpassListView(ListView):
    model = Outpass
    template_name = 'hostel/outpass_list.html'
    context_object_name = 'outpasses'

# Create View for Outpass
class OutpassCreateView(LoginRequiredMixin, CreateView):
    model = Outpass
    form_class = OutpassForm
    template_name = 'hostel/outpass_form.html'
    success_url = reverse_lazy('hostel:outpass_list')

    def form_valid(self, form):
        if not form.instance.requested_by_id:
            form.instance.requested_by = self.request.user
        messages.success(self.request, "✅ Outpass created.")
        return super().form_valid(form)

# Update View for Outpass (Approve/Reject)
class OutpassUpdateView(UpdateView):
    model = Outpass
    fields = ['student', 'reason', 'start_date', 'end_date', 'approved']
    template_name = 'hostel/outpass_form.html'
    success_url = reverse_lazy('hostel:outpass_list')

# Undo View for Outpass Edit
class UndoOutpassUpdateView(UpdateView):
    model = Outpass
    fields = ['student', 'reason', 'start_date', 'end_date', 'approved']
    template_name = 'hostel/outpass_form.html'
    success_url = reverse_lazy('hostel:outpass_list')

    def get_object(self, queryset=None):
        # Get the latest version of the outpass
        outpass = super().get_object(queryset)
        # Get the last history entry for this outpass (the most recent edit)
        last_history = outpass.history.latest('created_at')
        # Restore the outpass to the previous state from the history
        outpass.reason = last_history.reason
        outpass.start_date = last_history.start_date
        outpass.end_date = last_history.end_date
        outpass.approved = last_history.approved
        return outpass

    def form_valid(self, form):
        outpass = form.save(commit=False)
        outpass.save()  # Save the restored outpass
        return redirect(self.success_url)
