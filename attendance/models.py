# attendance/models.py
print('attendance models.py loaded')

from django.db import models
from django.utils import timezone
from students.models import Student
from staff.models import Staff
from exams.models import Term, Subject  # Importing Term and Subject from the exams app


class AttendanceType(models.TextChoices):
    PRESENT = 'Present', 'Present'
    ABSENT = 'Absent', 'Absent'
    LEAVE = 'Leave', 'Leave'
    HALF_DAY = 'Half Day', 'Half Day'



# ✅ STUDENT ATTENDANCE MODEL
class StudentAttendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=AttendanceType.choices, default=AttendanceType.PRESENT)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.admission_number} - {self.date} - {self.status}"

    @classmethod
    def bulk_create_attendance(cls, attendance_data):
        """
        Bulk insert student attendance records.
        attendance_data: list of dicts with keys matching model fields,
        e.g.: [{'student': student_obj, 'date': date_obj, 'status': status_str, 'remarks': remarks_str}]
        """
        attendance_objects = [cls(**data) for data in attendance_data]
        cls.objects.bulk_create(attendance_objects)


# ✅ STAFF ATTENDANCE MODEL



class StaffAttendance(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True, null=True)  # For grouping
    staff_role = models.CharField(max_length=100, blank=True, null=True)   # e.g., Teacher, Admin, etc.

    date = models.DateField(default=timezone.now)
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=AttendanceType.choices,
        default=AttendanceType.PRESENT
    )
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('staff', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.staff.full_name} - {self.date} - {self.status}"

    @classmethod
    def mark_attendance(cls, staff, status='Present', check_in=None, check_out=None, remarks=''):
        """
        Create or update attendance for staff.
        """
        obj, created = cls.objects.get_or_create(
            staff=staff,
            date=timezone.now().date(),
            defaults={
                'status': status,
                'check_in_time': check_in,
                'check_out_time': check_out,
                'remarks': remarks,
                'department': staff.department.name if staff.department else None,
                'staff_role': staff.staff_role if hasattr(staff, 'staff_role') else None
            }
        )
        return obj



# ✅ FUTURE INTEGRATION: BIOMETRIC PLACEHOLDER
class BiometricLog(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    device_id = models.CharField(max_length=100)
    log_type = models.CharField(max_length=50)  # e.g., check-in/check-out

    def __str__(self):
        return f"{self.timestamp} - {self.device_id}"


# ----------------------
# EXAM MARK AND RESULT MODELS (Integration with Term, Subject, ExamMark)
# Added related_name to avoid clashes with exams app
# ----------------------

class ExamMark(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_exammark_student'
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='attendance_exammark_term'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='attendance_exammark_subject'
    )
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, blank=True)
    remarks = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        percent = (self.marks_obtained / self.max_marks) * 100
        if percent >= 90:
            self.grade = "A+"
        elif percent >= 75:
            self.grade = "A"
        elif percent >= 60:
            self.grade = "B"
        elif percent >= 50:
            self.grade = "C"
        elif percent >= 35:
            self.grade = "D"
        else:
            self.grade = "F"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.term}"


# ✅ RESULT SUMMARY MODEL
class ResultSummary(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_resultsummary_student'
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='attendance_resultsummary_term'
    )
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    average = models.DecimalField(max_digits=5, decimal_places=2)
    rank = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.term} Summary"

    @classmethod
    def generate_summary(cls, term):
        """
        Generates summary for all students in the given term.
        """
        students = Student.objects.all()
        for student in students:
            marks = ExamMark.objects.filter(student=student, term=term)
            total_marks = sum([m.marks_obtained for m in marks])
            count = marks.count() or 1
            average = total_marks / count
            summary = cls.objects.create(
                student=student,
                term=term,
                total_marks=total_marks,
                average=average
            )
            summaries = list(cls.objects.filter(term=term).order_by('-average'))
            summary.rank = summaries.index(summary) + 1
            summary.save()


# ----------------------
# ATTENDANCE MODEL (Main Entry)
# ----------------------
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=[('Present', 'Present'), ('Absent', 'Absent')],
        default='Absent'
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)

    @classmethod
    def bulk_create_attendance(cls, attendance_data):
        """
        Bulk insert attendance records for generic Attendance.
        attendance_data: [{'student': Student, 'date': date, 'status': str, 'term': Term}]
        """
        attendance_objects = [cls(**data) for data in attendance_data]
        cls.objects.bulk_create(attendance_objects)
