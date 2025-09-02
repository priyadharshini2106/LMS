# Fully coded admin.py for certificates
print('certificates admin.py loaded')
from django.contrib import admin
from .models import CertificateRecord

@admin.register(CertificateRecord)
class CertificateRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'certificate_type', 'generated_on')
    list_filter = ('certificate_type', 'generated_on')
    search_fields = ('student__full_name',)
