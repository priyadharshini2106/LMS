from django import forms
from .models import Staff

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = '__all__'
        widgets = {
            # Will be read-only in form (if present)
            'staff_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doj': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'staff_category': forms.Select(attrs={'class': 'form-select'}),
            'staff_role': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'rfid_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Scan or enter RFID code'
            }),
            'biometric_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Biometric ID'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False  # ✅ base64 image upload not mandatory

        # If the staff_id field exists, disable editing
        if 'staff_id' in self.fields:
            self.fields['staff_id'].disabled = True
            if not self.instance.pk:
                # Show a hint for new staff
                self.fields['staff_id'].initial = 'Will be generated automatically'
