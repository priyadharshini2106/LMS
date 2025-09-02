print('staff models.py loaded')
from django.db import models, transaction, ProgrammingError, OperationalError
from django.utils import timezone
from django.contrib.auth import get_user_model

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class Designation(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.title

class StaffIDSequence(models.Model):
    """Keeps the last sequence per (department, designation) to avoid race conditions."""
    department = models.CharField(max_length=30, choices=[
        ('SCIENCE', 'Science'),
        ('MATHS', 'Mathematics'),
        ('ENGLISH', 'English'),
        ('SOCIAL', 'Social Studies'),
        ('ACCOUNTS', 'Accounts'),
        ('OFFICE', 'Office Department'),
        ('TRANSPORT', 'Transport'),
        ('OTHERS', 'Others'),
    ])
    designation = models.CharField(max_length=30, choices=[
        ('PRINCIPAL', 'Principal'),
        ('TEACHER', 'Teacher'),
        ('CLERK', 'Office Clerk'),
        ('ACCOUNTANT', 'Accountant'),
        ('DRIVER', 'Driver'),
        ('SWEEPER', 'Sweeper'),
        ('GUARD', 'Security Guard'),
        ('HELPER', 'Helper'),
    ])
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('department', 'designation')

    def __str__(self):
        return f"{self.department}-{self.designation}: {self.last_number}"

class Staff(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    EMPLOYMENT_TYPE = [('Permanent', 'Permanent'), ('Contract', 'Contract'), ('Temporary', 'Temporary')]
    STATUS_CHOICES = [('Active', 'Active'), ('Resigned', 'Resigned'), ('Suspended', 'Suspended')]

    STAFF_CATEGORY_CHOICES = [
        ('TEACHER', 'Teacher'), ('OFFICE', 'Office Staff'), ('DRIVER', 'Driver'),
        ('CLEANER', 'Sanitary Cleaner'), ('SECURITY', 'Security Guard'),
        ('ADMIN', 'Administrative / Management'), ('NON_TEACHING', 'Non-Teaching Staff'),
        ('OTHERS', 'Others'),
    ]
    ROLE_CHOICES = [
        ('PRINCIPAL', 'Principal / CEO'), ('HR', 'HR / Admin Officer'),
        ('TEACHER', 'Teacher'), ('OFFICE', 'Office Staff'),
    ]
    DEPARTMENT_CHOICES = [
        ('SCIENCE', 'Science'), ('MATHS', 'Mathematics'), ('ENGLISH', 'English'),
        ('SOCIAL', 'Social Studies'), ('ACCOUNTS', 'Accounts'), ('OFFICE', 'Office Department'),
        ('TRANSPORT', 'Transport'), ('OTHERS', 'Others'),
    ]
    DESIGNATION_CHOICES = [
        ('PRINCIPAL', 'Principal'), ('TEACHER', 'Teacher'), ('CLERK', 'Office Clerk'),
        ('ACCOUNTANT', 'Accountant'), ('DRIVER', 'Driver'), ('SWEEPER', 'Sweeper'),
        ('GUARD', 'Security Guard'), ('HELPER', 'Helper'),
    ]

    department = models.CharField(max_length=30, choices=DEPARTMENT_CHOICES, default='OTHERS')
    designation = models.CharField(max_length=30, choices=DESIGNATION_CHOICES, default='TEACHER')

    # Auto-generated; users never edit this
    staff_id = models.CharField(max_length=30, unique=True, editable=False, blank=True)

    full_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob = models.DateField()
    doj = models.DateField(default=timezone.now)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to='staff_photos/', null=True, blank=True)
    rfid_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    biometric_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE, default='Permanent')
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    remarks = models.TextField(blank=True)

    staff_category = models.CharField(max_length=20, choices=STAFF_CATEGORY_CHOICES, default='TEACHER')
    staff_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TEACHER')

    user = models.OneToOneField(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.staff_id})"

    # Codes
    DEPT_CODES = {
        'SCIENCE': 'SCI', 'MATHS': 'MAT', 'ENGLISH': 'ENG', 'SOCIAL': 'SOC',
        'ACCOUNTS': 'ACC', 'OFFICE': 'OFF', 'TRANSPORT': 'TRN', 'OTHERS': 'OTH',
    }
    DESIG_CODES = {
        'PRINCIPAL': 'PRN', 'TEACHER': 'TEA', 'CLERK': 'CLK', 'ACCOUNTANT': 'ACC',
        'DRIVER': 'DRV', 'SWEEPER': 'SWP', 'GUARD': 'GRD', 'HELPER': 'HLP',
    }

    def _next_staff_id(self):
        """Prefer sequence table; if missing, fall back to 'max+1' per prefix."""
        dept_code = self.DEPT_CODES.get(self.department, (self.department or 'OTH')[:3].upper())
        desig_code = self.DESIG_CODES.get(self.designation, (self.designation or 'OTH')[:3].upper())
        prefix = f"{dept_code}-{desig_code}-"

        try:
            # Primary (race-safe) path
            with transaction.atomic():
                seq, _ = StaffIDSequence.objects.select_for_update().get_or_create(
                    department=self.department, designation=self.designation
                )
                seq.last_number += 1
                seq.save(update_fields=['last_number'])
                return f"{prefix}{seq.last_number:04d}"
        except (ProgrammingError, OperationalError):
            # Fallback: table missing or DB cannot lock — NOT race-safe, but avoids 500s
            last = (
                Staff.objects
                .filter(staff_id__startswith=prefix)
                .order_by('-staff_id')  # zero-padded, so string order works
                .first()
            )
            if last and last.staff_id:
                try:
                    n = int(last.staff_id.split('-')[-1]) + 1
                except ValueError:
                    n = 1
            else:
                n = 1
            return f"{prefix}{n:04d}"

    def save(self, *args, **kwargs):
        if not self.staff_id:
            if not self.department or not self.designation:
                raise ValueError("Department and Designation are required to generate staff_id.")
            self.staff_id = self._next_staff_id()
        super().save(*args, **kwargs)
