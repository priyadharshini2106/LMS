from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from students.models import Student

CustomUser = get_user_model()


# -------------------- Hostel --------------------
class Hostel(models.Model):
    GENDER_CHOICES = (
        ("M", "Boys"),
        ("F", "Girls"),
        ("C", "Co-ed"),
    )

    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=50, unique=True)
    capacity = models.PositiveIntegerField()
    gender_policy = models.CharField(max_length=1, choices=GENDER_CHOICES, default="C")
    warden_name = models.CharField(max_length=200, blank=True, null=True)
    warden_contact = models.CharField(max_length=20, blank=True, null=True)
    warden_image = models.ImageField(upload_to="warden_images/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


# -------------------- Room --------------------
class Room(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=10)  # e.g., 'A-101'
    floor = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("hostel", "room_number")
        indexes = [
            models.Index(fields=["hostel"]),
            models.Index(fields=["room_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.hostel.code}-{self.room_number}"


class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.CharField(max_length=10)  # e.g., 'B1', 'B2'
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ("room", "bed_number")
        indexes = [
            models.Index(fields=["room"]),
            models.Index(fields=["is_available"]),
        ]

    def __str__(self) -> str:
        return f"{self.room} / {self.bed_number}"


# -------------------- Allocation --------------------
class Allocation(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("VACATED", "Vacated"),
    )

    # Using OneToOneField ensures a bed can only have one active allocation at a time
    bed = models.OneToOneField(Bed, on_delete=models.CASCADE, related_name="allocation")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="hostel_allocations")
    date_allocated = models.DateField(auto_now_add=True)
    date_vacated = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")

    class Meta:
        ordering = ("-date_allocated",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["student"]),
        ]

    def clean(self):
        if self.status == "VACATED" and not self.date_vacated:
            raise ValidationError("Provide date_vacated when status is VACATED.")
        if self.status == "ACTIVE" and self.date_vacated:
            raise ValidationError("Active allocations cannot have date_vacated.")

    def __str__(self) -> str:
        return f"{self.student} → {self.bed}"


# -------------------- Hostel Payment --------------------
class HostelPayment(models.Model):
    METHOD_CHOICES = (
        ("CASH", "Cash"),
        ("CARD", "Card"),
        ("UPI", "UPI"),
        ("BANK", "Bank Transfer"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="hostel_payments")
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default="CASH")
    receipt_no = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        ordering = ("-payment_date",)
        indexes = [
            models.Index(fields=["payment_date"]),
            models.Index(fields=["student"]),
            models.Index(fields=["hostel"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.amount} on {self.payment_date}"


# -------------------- Visitor Log --------------------
class VisitorLog(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="visitors")
    admission_number = models.CharField(max_length=50, blank=True, null=True)
    student_name = models.CharField(max_length=150, blank=True, null=True)
    student_class = models.CharField(max_length=50, blank=True, null=True)
    visitor_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=50, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    visit_date = models.DateField()
    in_time = models.DateTimeField(auto_now_add=True)
    out_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-visit_date", "-in_time")
        indexes = [
            models.Index(fields=["hostel"]),
            models.Index(fields=["visit_date"]),
        ]

    def __str__(self) -> str:
        who = self.student_name or self.admission_number or "Unknown student"
        return f"{self.visitor_name} visiting {who}"


# -------------------- Outpass --------------------
class Outpass(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reason = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    approved = models.BooleanField(default=False)  # ← your views reference this
    requested_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self) -> str:
        return f"Outpass for {self.student} from {self.start_date} to {self.end_date}"


class OutpassHistory(models.Model):
    outpass = models.ForeignKey(Outpass, on_delete=models.CASCADE, related_name="history")
    reason = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["outpass"]),
        ]

    def __str__(self) -> str:
        return f"History of Outpass {self.outpass.student} on {self.created_at}"


# -------------------- Complaints --------------------
class Complaint(models.Model):
    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")

    class Meta:
        ordering = ("-date_created",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["date_created"]),
        ]

    def __str__(self) -> str:
        return f"Complaint by {self.student} on {self.date_created}"
