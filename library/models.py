# Fully coded models.py for library
print('library models.py loaded')
from django.db import models
from students.models import Student
from django.utils import timezone


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True)
    publisher = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} by {self.author}"


class BookIssue(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)

    def is_overdue(self):
        return self.return_date is None and timezone.now().date() > self.due_date

    def __str__(self):
        return f"{self.book.title} → {self.student.full_name}"
