print('students admin.py loaded')

from django.contrib import admin
from .models import Student, ClassSection, AcademicYear

# ------------------------------------------------------------------
# STUDENT ADMIN
# ------------------------------------------------------------------

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'admission_number', 'name', 'class_section', 'academic_year',
        'roll_no', 'gender', 'dob', 'status',
        'student_category', 'transport_mode', 'room_number',
        'rfid_code',
        'father_name', 'mother_name', 'contact_number','biometric_id',
    )

    list_filter = (
        'gender', 'status', 'academic_year', 'class_section',
        'community', 'religion',
        'student_category', 'transport_mode',
    )

    search_fields = (
        'name', 'admission_number', 'roll_no',
        'father_name', 'mother_name', 'aadhaar_number', 'rfid_code','biometric_id',
    )

    readonly_fields = ('admission_number', 'roll_no')
    ordering = ('-academic_year', 'class_section__class_name', 'class_section__section', 'roll_no')

# ------------------------------------------------------------------
# CLASS SECTION ADMIN
# ------------------------------------------------------------------

@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'section')
    search_fields = ('class_name', 'section')
    list_filter = ('class_name',)

# ------------------------------------------------------------------
# ACADEMIC YEAR ADMIN
# ------------------------------------------------------------------

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    search_fields = ('name',)
