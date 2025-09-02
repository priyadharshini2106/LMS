from django.db import models
from django.contrib.auth import get_user_model
from staff.models import Staff


User = get_user_model()

DAYS_OF_WEEK = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
]

MEDIUM_CHOICES = [
    ('Tamil', 'Tamil'),
    ('English', 'English'),
]

class ClassLevel(models.Model):
    name = models.CharField(max_length=20, unique=True)
    medium = models.CharField(max_length=10, choices=MEDIUM_CHOICES, default='Tamil')

    def __str__(self):
        return f"{self.name} ({self.medium})"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    is_special = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.class_level}"

class Period(models.Model):
    period_number = models.PositiveIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['period_number']
        unique_together = ('period_number', 'start_time', 'end_time')

    def __str__(self):
        return f"Period {self.period_number} ({self.start_time} - {self.end_time})"



class TimetableSlot(models.Model):
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Staff, on_delete=models.CASCADE, limit_choices_to={'staff_role': 'TEACHER'})

    class Meta:
        unique_together = ('class_level', 'day', 'period')
        ordering = ['class_level', 'day', 'period']

    def __str__(self):
        return f"{self.class_level} | {self.day} | {self.period} | {self.subject} | {self.teacher}"