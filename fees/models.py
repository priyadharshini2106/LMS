from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

# Helper function to get the default academic year
def get_default_academic_year():
    try:
        AcademicYear = models.apps.get_model('students', 'AcademicYear')
        return AcademicYear.objects.first().id
    except:
        return None

# fees/models.py
from django.db import models
from django.utils import timezone

class FeeCategory(models.Model):
    FEE_TYPE = [('mandatory', 'Mandatory'), ('optional', 'Optional')]
    APPLICABLE_TO = [
        ('all', 'All Students'),
        ('day_scholar', 'Day Scholar'),
        ('hosteller', 'Hosteller'),
        ('transport_user', 'Transport User'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    fee_type = models.CharField(max_length=10, choices=FEE_TYPE, default='mandatory')
    # NOTE: no `choices=` here so values like "sec:ID" are allowed
    applicable_to = models.CharField(max_length=50, default='all')
    is_refundable = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_fee_type_display()})"

    @property
    def applicable_to_display(self):
        """Human-readable label for 'applicable_to' including class/section values."""
        val = self.applicable_to or ''
        # 1) static labels
        static_map = dict(self.APPLICABLE_TO)
        if val in static_map:
            return static_map[val]

        # 2) dynamic class-section value like "sec:123"
        if isinstance(val, str) and val.startswith('sec:'):
            try:
                pk = int(val.split(':', 1)[1])
            except (ValueError, IndexError):
                return val
            from students.models import ClassSection  # local import to avoid circular
            cs = ClassSection.objects.filter(pk=pk).first()
            return f"{cs.class_name}-{cs.section}" if cs else "Class Section (missing)"

        # 3) fallback (unknown custom values)
        return val


class FeeStructure(models.Model):
    # Let the user choose the academic year; don't try to auto-default to a possibly-missing one
    academic_year = models.ForeignKey('students.AcademicYear', on_delete=models.CASCADE)

    class_name = models.CharField(max_length=50)
    medium = models.CharField(max_length=20, choices=[('English', 'English'), ('Tamil', 'Tamil')])
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    due_date = models.DateField()
    installments = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    is_hostel_related = models.BooleanField(default=False)
    is_transport_related = models.BooleanField(default=False)

    class Meta:
        # same uniqueness rule, expressed with a named constraint
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'class_name', 'medium', 'fee_category'],
                name='uniq_fee_structure'
            )
        ]

    def __str__(self):
        return f"{self.class_name} - {self.fee_category.name} ({self.academic_year})"

class StudentFeeAssignment(models.Model):
    # fees/models.py
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="fee_assignments")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    assigned_on = models.DateField(auto_now_add=True)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_fully_paid = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['fee_structure']),
        ]

    def __str__(self):
        return f"{self.student.name} | {self.fee_structure.fee_category.name} | ₹{self.final_amount}"

    def balance_amount(self):
        return self.final_amount - self.paid_amount

    def add_payment(self, amount):
        if amount + self.paid_amount > self.final_amount:
            raise ValueError("❌ Payment exceeds total final amount.")
        self.paid_amount += amount
        if self.paid_amount >= self.final_amount:
            self.is_fully_paid = True
        self.save()

from decimal import Decimal

@property
def balance_amount(self):
    final_amt = self.final_amount or Decimal('0.00')
    paid_amt  = self.paid_amount  or Decimal('0.00')
    return final_amt - paid_amt


# models.py
from datetime import date
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from fees.models import StudentFeeAssignment

class FeePayment(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Cheque', 'Cheque'),
        ('NEFT', 'NEFT'),
        ('Online', 'Online'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, null=True, blank=True)
    # Use a string reference + related_name for clarity
    fee_assignment = models.ForeignKey(
        'fees.StudentFeeAssignment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='payments',
    )

    receipt_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
    payment_date = models.DateField(default=date.today)  # ✅
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='Cash')
    remarks = models.TextField(blank=True, null=True)
    processed_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=['student'])]

    def __str__(self):
        name = getattr(self.student, "name", "Unknown")
        return f"{self.receipt_no} - {name} - ₹{self.amount_paid}"

    def save(self, *args, **kwargs):
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

# models.py
from django.core.exceptions import ValidationError

@receiver(post_save, sender=FeePayment)
def update_assignment_balance(sender, instance, created, **kwargs):
    if created and instance.fee_assignment:
        try:
            instance.fee_assignment.add_payment(instance.amount_paid)
        except ValueError:
            # Safety: do not crash the request. The form validation should prevent this,
            # so this is just a final safeguard (race conditions etc.).
            # Optionally log here.
            pass

class InstallmentPayment(models.Model):
    fee_payment = models.ForeignKey(FeePayment, on_delete=models.CASCADE)
    installment_number = models.PositiveIntegerField()
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Installment {self.installment_number} for {self.fee_payment.student.name}"

class FeeConcession(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    concession_type = models.CharField(max_length=50)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.concession_type}"

class FeeReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('summary', 'Summary'),
        ('detailed', 'Detailed'),
    ]

    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    generated_by = models.CharField(max_length=100)
    generated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type} report by {self.generated_by}"

class FeeReminder(models.Model):
    REMINDER_TYPES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('call', 'Phone Call'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=10, choices=REMINDER_TYPES)
    message = models.TextField()
    send_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.reminder_type} to {self.student.name} on {self.send_date}"
    
from django.db import models
from django.utils import timezone
from students.models import Student, AcademicYear

class FeeSMSHistory(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    phone_number = models.CharField(max_length=15)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Fee SMS History'
        verbose_name_plural = 'Fee SMS History'
    
    def __str__(self):
        return f"SMS to {self.student.name} at {self.sent_at}"