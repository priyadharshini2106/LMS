# Fully coded models.py for certificates
print('certificates models.py loaded')
from django.db import models
from students.models import Student

class CertificateRecord(models.Model):
    CERTIFICATE_TYPES = [
        ('bonafide', 'Bonafide'),
        ('transfer', 'Transfer Certificate'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)
    generated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.get_certificate_type_display()}"
