from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime

from .models import (
    Hostel, Room, Bed, Allocation,
    HostelPayment, VisitorLog,
    Outpass, OutpassHistory,
    Complaint,
)

# =========================
# Hostel
# =========================
@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "capacity", "gender_policy", "warden_name", "warden_contact")
    search_fields = ("name", "code", "warden_name", "warden_contact")
    list_filter = ("gender_policy",)
    ordering = ("name",)


# =========================
# Room
# =========================
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("hostel", "room_number", "floor", "total_beds")
    search_fields = ("hostel__name", "hostel__code", "room_number")
    list_filter = ("hostel", "floor")

    @admin.display(description="Total Beds")
    def total_beds(self, obj):
        return obj.beds.count()


# =========================
# Bed
# =========================
@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ("room", "bed_number", "is_available")
    list_filter = ("is_available", "room__hostel")
    search_fields = ("room__room_number", "bed_number", "room__hostel__name")


# =========================
# Allocation
# =========================
@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ("student", "bed", "status", "date_allocated", "date_vacated")
    search_fields = ("student__name", "student__admission_number", "bed__room__hostel__name", "bed__room__room_number", "bed__bed_number")
    list_filter = ("status", "bed__room__hostel")
    date_hierarchy = "date_allocated"
    ordering = ("-date_allocated",)


# =========================
# Hostel Payment
# =========================
@admin.register(HostelPayment)
class HostelPaymentAdmin(admin.ModelAdmin):
    list_display = ("allocation_info", "student", "hostel", "amount", "method", "payment_date", "receipt_no")
    list_filter = ("method", "payment_date", "hostel")
    search_fields = ("student__name", "student__admission_number", "hostel__name", "receipt_no")
    date_hierarchy = "payment_date"
    ordering = ("-payment_date",)

    @admin.display(description="Allocation")
    def allocation_info(self, obj):
        """
        Show the student's active bed in this hostel, if any.
        """
        alloc = obj.student.hostel_allocations.filter(
            bed__room__hostel=obj.hostel, status="ACTIVE"
        ).select_related("bed", "bed__room").first()
        return alloc.bed if alloc else "No allocation"


# =========================
# Visitor Log
# =========================
@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = (
        "visitor_name",
        "student_name",
        "student_class",
        "admission_number",
        "hostel",
        "visit_date",
        "in_time_local",
        "out_time_local",
    )
    list_filter = ("visit_date", "hostel")
    search_fields = ("visitor_name", "student_name", "admission_number", "hostel__name")
    date_hierarchy = "visit_date"
    ordering = ("-visit_date", "-in_time")

    @admin.display(description="In time")
    def in_time_local(self, obj):
        return localtime(obj.in_time).strftime("%Y-%m-%d %H:%M") if obj.in_time else "—"

    @admin.display(description="Out time")
    def out_time_local(self, obj):
        return localtime(obj.out_time).strftime("%Y-%m-%d %H:%M") if obj.out_time else "—"


# =========================
# Outpass & History
# =========================
class OutpassHistoryInline(admin.TabularInline):
    model = OutpassHistory
    extra = 0
    readonly_fields = ("reason", "start_date", "end_date", "approved", "created_at")
    can_delete = False


@admin.register(Outpass)
class OutpassAdmin(admin.ModelAdmin):
    list_display = ("student", "status_badge", "approved", "start_date", "end_date", "requested_by")
    list_filter = ("status", "approved")
    search_fields = ("student__name", "student__admission_number", "requested_by__username")
    date_hierarchy = "start_date"
    inlines = [OutpassHistoryInline]
    ordering = ("-start_date",)

    @admin.display(description="Status")
    def status_badge(self, obj):
        color = {
            "Pending": "#f59e0b",     # amber
            "Approved": "#10b981",    # emerald
            "Rejected": "#ef4444",    # red
        }.get(obj.status, "#6b7280")   # gray
        return format_html(
            '<span style="padding:.2rem .5rem;border-radius:999px;background:{}20;color:{};font-weight:700;">{}</span>',
            color, color, obj.status
        )

    # Quick actions
    @admin.action(description="Mark selected as Approved")
    def make_approved(self, request, queryset):
        queryset.update(status="Approved", approved=True)

    @admin.action(description="Mark selected as Rejected")
    def make_rejected(self, request, queryset):
        queryset.update(status="Rejected", approved=False)

    actions = ["make_approved", "make_rejected"]


# =========================
# Complaint
# =========================
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("student", "status", "date_created", "short_desc")
    list_filter = ("status", "date_created")
    search_fields = ("student__name", "student__admission_number", "description")
    date_hierarchy = "date_created"
    ordering = ("-date_created",)

    @admin.display(description="Description")
    def short_desc(self, obj):
        return (obj.description[:60] + "…") if len(obj.description or "") > 60 else (obj.description or "—")
