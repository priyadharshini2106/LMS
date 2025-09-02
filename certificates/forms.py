# Fully coded forms.py for certificates
print('certificates forms.py loaded')
from django import forms
from students.models import Student

class CertificateRequestForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    certificate_type = forms.ChoiceField(
        choices=[('bonafide', 'Bonafide Certificate'), ('transfer', 'Transfer Certificate')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
