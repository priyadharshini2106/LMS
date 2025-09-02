from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import FeeCategory, FeeStructure, StudentFeeAssignment, FeePayment
from .services import FeeAssignmentService
from .forms import (
    FeeCategoryForm,
    FeeStructureForm,
    StudentFeeAssignmentForm,
    FeePaymentForm
)
from students.models import Notification

# ---------- FEE CATEGORY ----------
def fee_category_list(request):
    categories = FeeCategory.objects.all()
    return render(request, 'fees/fee_category_list.html', {'categories': categories})

def add_fee_category(request):
    form = FeeCategoryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Fee Category added successfully.")
            return redirect('fees:fee_category_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/fee_category_form.html', {'form': form})

def edit_fee_category(request, pk):
    category = get_object_or_404(FeeCategory, pk=pk)
    form = FeeCategoryForm(request.POST or None, instance=category)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Fee Category updated successfully.")
            return redirect('fees:fee_category_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/fee_category_form.html', {'form': form})

# ---------- FEE STRUCTURE ----------
def fee_structure_list(request):
    structures = FeeStructure.objects.all()
    return render(request, 'fees/fee_structure_list.html', {'structures': structures})

def add_fee_structure(request):
    form = FeeStructureForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Fee Structure added successfully.")
            return redirect('fees:fee_structure_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/fee_structure_form.html', {'form': form})

def edit_fee_structure(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)
    form = FeeStructureForm(request.POST or None, instance=structure)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Fee Structure updated successfully.")
            return redirect('fees:fee_structure_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/fee_structure_form.html', {'form': form})

# ---------- STUDENT FEE ASSIGNMENT ----------
def student_fee_assignment_list(request):
    assignments = StudentFeeAssignment.objects.all()
    return render(request, 'fees/student_fee_assignment_list.html', {'assignments': assignments})

# views.py (only the save bits change)
from django.contrib.contenttypes.models import ContentType
from students.models import Notification
from .models import StudentFeeAssignment

def assign_fee_to_student(request):
    form = StudentFeeAssignmentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            obj = form.save(commit=False)
            obj.is_fully_paid = (obj.final_amount or 0) > 0 and (obj.paid_amount or 0) >= (obj.final_amount or 0)
            obj.save()

            # ✅ Create notification for the student
            Notification.objects.create(
    student=obj.student,
    title=f"Fees assigned: {obj.fee_structure.name}",
    body=f"Final amount: ₹{(obj.final_amount or 0):,.2f}. Paid: ₹{(obj.paid_amount or 0):,.2f}.",
    content_type=ContentType.objects.get_for_model(StudentFeeAssignment),
    object_id=str(obj.pk),
)

            messages.success(request, "Fee assigned to student successfully.")
            return redirect('fees:student_fee_assignment_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/student_fee_assignment_form.html', {'form': form})

from students.models import Notification   # make sure this import is present

def edit_student_fee_assignment(request, pk):
    assignment = get_object_or_404(StudentFeeAssignment, pk=pk)
    form = StudentFeeAssignmentForm(request.POST or None, instance=assignment)
    if request.method == 'POST':
        if form.is_valid():
            obj = form.save(commit=False)
            obj.is_fully_paid = (obj.paid_amount or 0) >= (obj.final_amount or 0) and obj.final_amount > 0
            obj.save()

            # ✅ Create an "updated" notification
            Notification.objects.create(
    student=obj.student,
    title=f"Fees updated: {obj.fee_structure.name}",
    body=f"Final amount: ₹{(obj.final_amount or 0):,.2f}, Paid: ₹{(obj.paid_amount or 0):,.2f}.",
    content_type=ContentType.objects.get_for_model(StudentFeeAssignment),
    object_id=str(obj.pk),
)

            messages.success(request, "Assignment updated successfully.")
            return redirect('fees:student_fee_assignment_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/student_fee_assignment_form.html', {'form': form})

from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect

@require_POST
def delete_student_fee_assignment(request, pk):
    assignment = get_object_or_404(StudentFeeAssignment, pk=pk)

    # If you want to prevent deleting paid records:
    if (assignment.paid_amount or 0) > 0:
        messages.error(request, "Cannot delete: payments recorded for this assignment.")
        return redirect('fees:student_fee_assignment_list')

    try:
        # If you use a soft-delete library, see notes below.
        deleted_count, _ = StudentFeeAssignment.objects.filter(pk=pk).delete()
        if deleted_count:
            messages.success(request, "Assignment deleted permanently.")
        else:
            messages.error(request, "Nothing was deleted (record not found).")
    except ProtectedError:
        messages.error(request, "Cannot delete: related records protect this assignment.")
    return redirect('fees:student_fee_assignment_list')

# ---------- FEE PAYMENT ----------
def fee_payment_list(request):
    payments = FeePayment.objects.all()
    return render(request, 'fees/fee_payment_list.html', {'payments': payments})

# views.py
# views.py
from .models import FeePayment, StudentFeeAssignment

# views.py
from .models import FeePayment, StudentFeeAssignment

def add_fee_payment(request):
    form = FeePaymentForm(request.POST or None)

    student_id = request.POST.get('student') or request.GET.get('student')
    if student_id:
        form.fields['fee_assignment'].queryset = StudentFeeAssignment.objects.filter(student_id=student_id)
    else:
        # ✅ show all assignments when no student chosen yet
        form.fields['fee_assignment'].queryset = StudentFeeAssignment.objects.all()

    if request.method == 'POST':
        if form.is_valid():
            payment = form.save()
            messages.success(request, "Fee payment recorded successfully.")
            return redirect('fees:fee_payment_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/fee_payment_form.html', {'form': form, 'title': 'Add Fee Payment'})


def save(self, *args, **kwargs):
    try:
        is_new = self._state.adding

        if not self.receipt_no:
            last = FeePayment.objects.order_by('-id').first()
            if last and last.receipt_no and last.receipt_no.startswith("REC"):
                try:
                    last_num = int(last.receipt_no.replace("REC", ""))
                    self.receipt_no = f"REC{last_num + 1:03d}"
                except ValueError:
                    self.receipt_no = "REC001"
            else:
                self.receipt_no = "REC001"

        super().save(*args, **kwargs)
    except Exception as e:
        print(f"Error saving FeePayment: {e}")  # Debug print
        raise

def edit_fee_payment(request, pk):
    payment = get_object_or_404(FeePayment, pk=pk)
    form = FeePaymentForm(request.POST or None, instance=payment)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Fee payment updated.")
            return redirect('fees:fee_payment_list')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'fees/fee_payment_form.html', {'form': form})

# Optional homepage for /fees/
def fees_home(request):
    return render(request, 'fees/fees_home.html')

def bulk_assign_view(request):
    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        fee_id = request.POST.get('fee_id')
        try:
            success = FeeAssignmentService.bulk_assign_by_class(
                class_name=class_name,
                fee_structure_id=fee_id
            )
            messages.success(request, f"Assigned to {success} students")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        return redirect('fee_dashboard')
    return render(request, 'fees/bulk_assign_form.html')

def delete_fee_structure(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        fee_structure.delete()
        messages.success(request, 'Fee structure deleted successfully!')
        return redirect('fees:fee_structure_list')
    return redirect('fees:fee_structure_list')

def bulk_assign_fee(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        try:
            success = FeeAssignmentService.bulk_assign_by_class(
                class_name=fee_structure.class_name,
                fee_structure_id=fee_structure.id
            )
            messages.success(request, f"Successfully assigned to {success} students")
            return redirect('fees:fee_structure_list')
        except Exception as e:
            messages.error(request, f"Error during bulk assignment: {str(e)}")
            return redirect('fees:fee_structure_list')
    context = {
        'fee_structure': fee_structure,
        'class_name': fee_structure.class_name,
    }
    return render(request, 'fees/bulk_assign_confirm.html', context)


# fees/views.py
from decimal import Decimal
from itertools import groupby

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.utils.functional import cached_property

from .models import StudentFeeAssignment
from students.models import Student, AcademicYear

def _build_cards_queryset(request):
    qs = (
        StudentFeeAssignment.objects
        .select_related(
            'student',
            'fee_structure',
            'fee_structure__fee_category',
            'fee_structure__academic_year',
        )
        .prefetch_related('payments')
        .order_by('student__roll_no', 'student__name', 'fee_structure__fee_category__name')
    )

    # optional filters
    ay = request.GET.get('academic_year')  # id
    class_name = (request.GET.get('class_name') or '').strip()
    medium = request.GET.get('medium')
    student_id = request.GET.get('student')

    if ay:
        qs = qs.filter(fee_structure__academic_year_id=ay)
    if class_name:
        qs = qs.filter(fee_structure__class_name__iexact=class_name)
    if medium:
        qs = qs.filter(fee_structure__medium=medium)
    if student_id:
        qs = qs.filter(student_id=student_id)

    return qs

def _group_into_cards(qs):
    """Group assignments by student and compute totals."""
    cards = []
    # groupby requires qs sorted by the key; we ordered by student above
    for student_id, rows in groupby(qs, key=lambda a: a.student_id):
        items = list(rows)
        student = items[0].student
        total_final = sum((a.final_amount or Decimal('0.00')) for a in items)
        total_paid  = sum((a.paid_amount  or Decimal('0.00')) for a in items)
        balance     = total_final - total_paid

        # flatten payments (optional, convenient for “Recent payments”)
        recent_payments = []
        for a in items:
            for p in getattr(a, 'payments').all():
                recent_payments.append(p)
        recent_payments.sort(key=lambda p: (p.payment_date, p.id), reverse=True)

        cards.append({
            'student': student,
            'items': items,
            'total_final': total_final,
            'total_paid': total_paid,
            'balance': balance,
            'recent_payments': recent_payments[:5],  # show last 5
        })
    return cards

def fee_cards_report(request):
    qs = _build_cards_queryset(request)
    cards = _group_into_cards(qs)
    context = {
        'cards': cards,
        'academic_years': AcademicYear.objects.all(),
        'selected': {
            'academic_year': request.GET.get('academic_year') or '',
            'class_name': request.GET.get('class_name') or '',
            'medium': request.GET.get('medium') or '',
            'student': request.GET.get('student') or '',
        }
    }
    return render(request, 'fees/fee_cards_report.html', context)

def fee_card_detail(request, student_id: int):
    # optionally accept ?academic_year=&medium=&class_name=
    request_copy = request.GET.copy()
    request_copy['student'] = str(student_id)
    request.GET = request_copy  # safe because we return immediately
    return fee_cards_report(request)

# fees/views.py
# fees/views.py
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Sum, Value, Q
from django.db.models.functions import Coalesce
from django.urls import reverse

from students.models import Student, Notification, ClassSection, AcademicYear
from .models import StudentFeeAssignment

DEFAULT_TEMPLATE = (
    "Dear {name}, your fee balance is ₹{balance}. "
    "Adm No: {admission_no}, Roll: {roll_no}. Kindly pay at the earliest. - {school}"
)

def _render_tokens(tpl: str, ctx: dict) -> str:
    out = tpl
    for k, v in ctx.items():
        out = out.replace("{"+k+"}", str(v if v is not None else ""))
    return out

def _pending_rows(q=None, academic_year_id=None, class_name=None, section=None):
    qs = (
        StudentFeeAssignment.objects
        .select_related("student", "student__class_section", "fee_structure", "fee_structure__academic_year")
    )

    # optional filters
    if academic_year_id:
        qs = qs.filter(fee_structure__academic_year_id=academic_year_id)
    if class_name:
        qs = qs.filter(student__class_section__class_name__iexact=class_name)
    if section:
        qs = qs.filter(student__class_section__section__iexact=section)
    if q:
        qs = qs.filter(
            Q(student__name__icontains=q) |
            Q(student__admission_number__icontains=q) |
            Q(student__roll_no__icontains=q) |
            Q(student__contact_number__icontains=q)
        )

    qs = (
        qs.values(
            "student_id",
            "student__name",
            "student__admission_number",
            "student__roll_no",
            "student__contact_number",
            "student__class_section__class_name",
            "student__class_section__section",
        )
        .annotate(
            total_final=Coalesce(Sum("final_amount"), Value(0)),
            total_paid=Coalesce(Sum("paid_amount"), Value(0)),
        )
    )

    rows = []
    for r in qs:
        bal = (r["total_final"] or 0) - (r["total_paid"] or 0)
        if bal > 0:
            r["balance"] = bal
            rows.append(r)

    rows.sort(key=lambda x: (x["student__name"] or "", x["student__roll_no"] or ""))
    return rows

def _send_sms_stub(phone: str, text: str):
    # Replace with your real SMS gateway integration.
    print(f"[SMS] -> {phone}: {text}")

def fees_reminder_sms(request):
    # filters for GET and POST render
    ay  = request.GET.get("academic_year") or None
    cls = (request.GET.get("class_name") or "").strip() or None
    sec = (request.GET.get("section") or "").strip() or None
    q   = (request.GET.get("q") or "").strip() or None

    if request.method == "POST":
        tpl = (request.POST.get("message") or DEFAULT_TEMPLATE).strip()
        ids = request.POST.getlist("student_ids")
        if not ids:
            messages.error(request, "Please select at least one student.")
            return redirect("fees:fees_reminder_sms")

        rows = _pending_rows(q=q, academic_year_id=ay, class_name=cls, section=sec)
        by_id = {str(r["student_id"]): r for r in rows}
        sent = 0
        last_note_id = None
        last_student_id = None

        for sid in ids:
            try:
                s = Student.objects.select_related("class_section").get(pk=sid)
            except Student.DoesNotExist:
                continue

            r = by_id.get(str(sid), {})
            ctx = {
                "name": s.name,
                "admission_no": s.admission_number,
                "roll_no": s.roll_no,
                "class": getattr(s.class_section, "class_name", ""),
                "section": getattr(s.class_section, "section", ""),
                "balance": f"{r.get('balance', 0):,.2f}",
                "school": "Your School",  # put your real school name
            }
            text = _render_tokens(tpl, ctx)

            if s.contact_number:
                _send_sms_stub(s.contact_number, text)
                sent += 1

            note = Notification.objects.create(
                student=s,
                title="Fee Reminder SMS sent",
                body=text,  # <-- the exact SMS content
                link_url=reverse("fees:fee_cards_report") + f"?student={s.id}",
            )
            last_note_id = note.id
            last_student_id = s.id

        messages.success(request, f"Sent {sent} reminder(s).")
        # If exactly one student selected, jump straight to their notifications and highlight new one
        if len(ids) == 1 and last_student_id and last_note_id:
            url = reverse("student_notifications", args=[last_student_id])
            return redirect(f"{url}?focus={last_note_id}")

        return redirect("fees:fees_reminder_sms")

    # GET
    context = {
        "default_template": DEFAULT_TEMPLATE,
        "rows": _pending_rows(q=q, academic_year_id=ay, class_name=cls, section=sec),
        "academic_years": AcademicYear.objects.all(),
        "class_sections": ClassSection.objects.all(),
    }
    return render(request, "fees/fees_reminder_sms.html", context)

from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from django.contrib import messages
from django.conf import settings

from .models import StudentFeeAssignment
from .services import send_sms
from students.models import Student, Notification, ClassSection, AcademicYear
from django.urls import reverse
from students.models import Notification, Student

def _aggregate_pending_queryset(request):
    """
    Returns list of dicts with per-student totals (only balance > 0).
    Optional GET filters: academic_year (id), class_name, section, q (search).
    """
    ay = request.GET.get("academic_year")
    class_name = (request.GET.get("class_name") or "").strip()
    section = (request.GET.get("section") or "").strip()
    q = (request.GET.get("q") or "").strip()

    qs = (
        StudentFeeAssignment.objects
        .select_related("student", "fee_structure", "fee_structure__academic_year", "student__class_section")
        .values(
            "student_id",
            "student__name",
            "student__admission_number",
            "student__roll_no",
            "student__contact_number",
            "student__class_section__class_name",
            "student__class_section__section",
        )
    )
    if ay:
        qs = qs.filter(fee_structure__academic_year_id=ay)
    if class_name:
        qs = qs.filter(student__class_section__class_name__iexact=class_name)
    if section:
        qs = qs.filter(student__class_section__section__iexact=section)
    if q:
        qs = qs.filter(
            Q(student__name__icontains=q) |
            Q(student__admission_number__icontains=q) |
            Q(student__roll_no__icontains=q) |
            Q(student__contact_number__icontains=q)
        )

    qs = qs.annotate(
        total_final=Sum("final_amount"),
        total_paid=Sum("paid_amount"),
    ).annotate(
        balance=ExpressionWrapper(
            F("total_final") - F("total_paid"),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    ).filter(balance__gt=0).order_by("student__name")

    return list(qs)

def _render_message(template: str, student: Student, row: dict, school_name: str) -> str:
    """
    Merge placeholders in message template.
    {name}, {admission_no}, {roll_no}, {class}, {section}, {balance}, {school}
    """
    data = {
        "name": student.name,
        "admission_no": student.admission_number or "",
        "roll_no": student.roll_no or "",
        "class": row.get("student__class_section__class_name") or "",
        "section": row.get("student__class_section__section") or "",
        "balance": f"{row.get('balance') or Decimal('0.00'):.2f}",
        "school": school_name,
    }
    try:
        return template.format_map({k: (v or "") for k, v in data.items()})
    except KeyError:
        return template  # if unknown token appears, leave as-is

@login_required
def fees_reminder_sms(request):
    school_name = getattr(settings, "SCHOOL_NAME", "Our School")

    if request.method == "POST":
        msg_template = (request.POST.get("message") or "").strip()
        selected = request.POST.getlist("student_ids")

        if not msg_template:
            messages.error(request, "Please enter a message.")
            return redirect("fees:fees_reminder_sms")
        if not selected:
            messages.error(request, "Select at least one student.")
            return redirect("fees:fees_reminder_sms")

        pending_rows = _aggregate_pending_queryset(request)
        rows_by_id = {str(r["student_id"]): r for r in pending_rows}

        sent = failed = 0
        for sid in selected:
            row = rows_by_id.get(sid)
            student = Student.objects.filter(pk=sid).select_related("class_section").first()
            if not (row and student and student.contact_number):
                failed += 1
                continue

            message = _render_message(msg_template, student, row, school_name)
            if send_sms(student.contact_number, message):
                try:
                    Notification.objects.create(
                        student=student,
                        title="Fee Reminder SMS sent",
                        body=rendered,
                        link_url=reverse("fees:fee_cards_report") + f"?student={student.id}",  # optional
)
                except Exception:
                    pass
                sent += 1
            else:
                failed += 1

        if sent: messages.success(request, f"SMS sent to {sent} student(s).")
        if failed: messages.warning(request, f"Failed for {failed} student(s).")
        return redirect("fees:fees_reminder_sms")

    # GET
    rows = _aggregate_pending_queryset(request)
    return render(request, "fees/fees_reminder_sms.html", {
        "rows": rows,
        "academic_years": AcademicYear.objects.all(),
        "class_sections": ClassSection.objects.all().order_by("class_name", "section"),
        "default_template": "Dear {name}, your fee balance is ₹{balance}. Please pay at the earliest. – {school}",
    })
