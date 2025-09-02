from django.db import models
from django.db.models import Sum, Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from students.models import Student
from students.models import ClassSection

# Get the custom user model from settings
User = settings.AUTH_USER_MODEL

class Term(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name
    

class ClassLevel(models.Model):
    name = models.CharField(max_length=20)
    medium = models.CharField(max_length=20, choices=[('Tamil', 'Tamil'), ('English', 'English')])

    def __str__(self):
        return f"{self.name} ({self.medium})"
    
class ClassSection(models.Model):
    name = models.CharField(max_length=50)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name='sections')


from django.db import models
from django.core.exceptions import ObjectDoesNotExist  # add this

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)

    # IMPORTANT: point to the students app explicitly
    class_level = models.ForeignKey(
        'students.ClassSection',       # ← not 'ClassSection' and not exams.ClassSection
        on_delete=models.CASCADE,
        related_name='subjects',
    )

    def __str__(self):
        # Be defensive so a broken FK doesn't crash templates
        try:
            return f"{self.name} - {self.class_level}"
        except ObjectDoesNotExist:
            return self.name


class ExamRoom(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.IntegerField()
    building = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.building})"

class ExamType(models.Model):
    name = models.CharField(max_length=50)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    def __str__(self):
        return self.name

class ExamSchedule(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('graded', 'Graded'),
        ('published', 'Published'),
    ]
    
    class_level = models.ForeignKey('students.ClassSection', on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    exam_type = models.ForeignKey(ExamType, on_delete=models.PROTECT,null=True)
    exam_name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_date = models.DateField()
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    room = models.ForeignKey(ExamRoom, on_delete=models.SET_NULL, null=True, blank=True)
    invigilator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    class Meta:
        ordering = ['exam_date']
        permissions = [
            ('can_publish_exams', 'Can publish exam schedules'),
        ]

    def __str__(self):
        return f"{self.exam_name} - {self.class_level} - {self.subject}"

class QuestionPaper(models.Model):
    exam_schedule = models.OneToOneField(ExamSchedule, on_delete=models.CASCADE)
    setter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verified = models.BooleanField(default=False)
    storage_path = models.FileField(upload_to='question_papers/')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QP for {self.exam_schedule}"

class GradeScale(models.Model):
    name = models.CharField(max_length=50)
    minimum_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    description = models.CharField(max_length=100)

    class Meta:
        ordering = ['-minimum_percentage']

    def __str__(self):
        return f"{self.grade} ({self.minimum_percentage}%)"

from decimal import Decimal

class ExamMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.SET_NULL, null=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, blank=True)
    remarks = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['student', 'term']),
            models.Index(fields=['term', 'subject']),
        ]
        permissions = [
            ('can_enter_marks', 'Can enter exam marks'),
            ('can_verify_marks', 'Can verify exam marks'),
        ]

    def save(self, *args, **kwargs):
        if self.max_marks and self.max_marks > 0:
            percent = (self.marks_obtained / self.max_marks) * Decimal('100')
            grade_scale = GradeScale.objects.filter(
                minimum_percentage__lte=percent
            ).order_by('-minimum_percentage').first()
            self.grade = grade_scale.grade if grade_scale else 'F'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.marks_obtained}/{self.max_marks}"

class MarkEntryVerification(models.Model):
    exam_mark = models.OneToOneField(ExamMark, on_delete=models.CASCADE)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='entered_marks')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verified_marks')
    verification_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Verification for {self.exam_mark}"

class ExamAbsence(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE)
    reason = models.TextField()
    documented = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approval_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Exam absences"

    def __str__(self):
        return f"{self.student} absent for {self.exam_schedule}"

class ResultSummary(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    average = models.DecimalField(max_digits=5, decimal_places=2)
    rank = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Result summaries"
        ordering = ['term', 'rank']

    def __str__(self):
        return f"{self.student} - {self.term} Summary (Rank: {self.rank})"

class ResultPublication(models.Model):
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    publish_date = models.DateTimeField()
    message_to_parents = models.TextField()
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"Results published for {self.term} on {self.publish_date}"

@receiver(post_save, sender=ExamMark)
@receiver(post_delete, sender=ExamMark)
def update_result_summary(sender, instance, **kwargs):
    student = instance.student
    term = instance.term
    
    marks = ExamMark.objects.filter(student=student, term=term)
    
    total_marks = marks.aggregate(total=Sum('marks_obtained'))['total'] or 0
    average = marks.aggregate(avg=Avg('marks_obtained'))['avg'] or 0
    
    summary, created = ResultSummary.objects.get_or_create(
        student=student,
        term=term,
        defaults={
            'total_marks': total_marks,
            'average': average,
            'rank': None
        }
    )
    
    if not created:
        summary.total_marks = total_marks
        summary.average = average
        summary.save()
    
    update_term_ranks(term)

def update_term_ranks(term):
    summaries = ResultSummary.objects.filter(term=term).order_by('-average')
    for rank, summary in enumerate(summaries, start=1):
        if summary.rank != rank:
            summary.rank = rank
            summary.save(update_fields=['rank'])