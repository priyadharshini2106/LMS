from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Choice constants
GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
)

RELIGION_CHOICES = (
    ('Hindu', 'Hindu'),
    ('Christian', 'Christian'),
    ('Muslim', 'Muslim'),
)

COMMUNITY_CHOICES = (
    ('OC', 'OC'),
    ('BC', 'BC'),
    ('MBC', 'MBC'),
    ('SC', 'SC'),
    ('ST', 'ST'),
    ('FC', 'FC'),
)

STATUS_CHOICES = (
    ('Active', 'Active'),
    ('Alumni', 'Alumni'),
    ('Left', 'Left'),
)


class AcademicYear(models.Model):
    name = models.CharField(max_length=10, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name


class ClassSection(models.Model):
    class_name = models.CharField(max_length=20)
    section = models.CharField(max_length=5)

    class Meta:
        unique_together = ('class_name', 'section')

    def __str__(self):
        return f"{self.class_name} - {self.section}"
    
# students/models.py
from django.db import models

class StudentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name



class Student(models.Model):
    admission_number = models.CharField(max_length=20, unique=True, blank=True)
    roll_no = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob = models.DateField(verbose_name="Date of Birth")

    class_section = models.ForeignKey(ClassSection, on_delete=models.SET_NULL, null=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)

    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_relation = models.CharField(max_length=50, blank=True, null=True)

    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)
    religion = models.CharField(max_length=20, choices=RELIGION_CHOICES, blank=True)
    community = models.CharField(max_length=10, choices=COMMUNITY_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)

    date_joined = models.DateField(default=timezone.now)
    date_of_leaving = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')

    previous_school = models.CharField(max_length=255, blank=True, null=True)
    transfer_certificate_number = models.CharField(max_length=50, blank=True, null=True)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)

    # Optional Fields
    rfid_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    biometric_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    STUDENT_CATEGORY_CHOICES = [
        ('day_scholar', 'Day Scholar'),
        ('hosteller', 'Hosteller'),
    ]
    student_category = models.CharField(
        max_length=20,
        choices=STUDENT_CATEGORY_CHOICES,
        default='day_scholar'
    )

    TRANSPORT_MODE_CHOICES = [
        ('school_bus', 'School Bus'),
        ('private_van', 'Private Van'),
        ('auto', 'Auto'),
        ('own_vehicle', 'Own Vehicle'),
        ('walk', 'Walk'),
        ('other', 'Other'),
    ]
    transport_mode = models.CharField(max_length=20, choices=TRANSPORT_MODE_CHOICES, blank=True, null=True)
    pickup_point = models.CharField(max_length=100, blank=True, null=True)
    bus_route_number = models.CharField(max_length=20, blank=True, null=True)

    hostel_name = models.CharField(max_length=100, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        current_year = timezone.now().year

        if self.class_section:
            class_code = self.class_section.class_name
            section_code = self.class_section.section
        else:
            class_code = ''
            section_code = ''

        if not self.roll_no and self.class_section:
            existing_rolls = Student.objects.filter(class_section=self.class_section)
            next_roll_number = existing_rolls.count() + 1
            self.roll_no = f"{class_code}{section_code}{next_roll_number:02d}"

        if not self.admission_number and self.roll_no:
            self.admission_number = f"PK{current_year}-{self.roll_no}"

        super().save(*args, **kwargs)

    @property
    def class_name(self):
        return self.class_section.class_name if self.class_section else None

    @property
    def section(self):
        return self.class_section.section if self.class_section else None

    def __str__(self):
        return f"{self.admission_number} - {self.name}"
    
class Notification(models.Model):
    student = models.ForeignKey('Student', related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    body = models.TextField(blank=True)
    link_url = models.CharField(max_length=255, blank=True)  # optional: where to send user
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # optional: reference to any related object (like a fee assignment)
    content_type = models.ForeignKey('contenttypes.ContentType', null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.CharField(max_length=64, blank=True, null=True)

    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.student.name}] {self.title}"