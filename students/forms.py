from django import forms
from .models import Student, ClassSection, AcademicYear

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude=['admission_number', 'roll_no']
        fields = [
            'admission_number', 'roll_no', 'name', 'gender', 'dob',
            'class_section', 'academic_year',
            'father_name', 'mother_name', 'guardian_name', 'guardian_relation',
            'address', 'contact_number', 'email',
            'aadhaar_number', 'religion', 'community', 'blood_group',
            'photo', 'previous_school', 'transfer_certificate_number',
            'date_of_leaving', 'status',
            'rfid_code', 'student_category',
            'transport_mode', 'pickup_point', 'bus_route_number',
            'hostel_name', 'room_number', 'biometric_id',
        ]

        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_of_leaving': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'admission_number': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'roll_no': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'rfid_code': forms.TextInput(attrs={'placeholder': 'Scan or enter RFID', 'class': 'form-control'}),
            'pickup_point': forms.TextInput(attrs={'placeholder': 'Pickup Location', 'class': 'form-control'}),
            'bus_route_number': forms.TextInput(attrs={'placeholder': 'Route No', 'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'placeholder': 'Room No', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'class_section': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            # Add similar class attributes for other fields
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set querysets for foreign key fields
        self.fields['class_section'].queryset = ClassSection.objects.all()
        self.fields['academic_year'].queryset = AcademicYear.objects.all()
        
        # Make fields required
        self.fields['name'].required = True
        self.fields['gender'].required = True
        self.fields['dob'].required = True
        self.fields['father_name'].required = True
        self.fields['mother_name'].required = True
        self.fields['address'].required = True
        self.fields['contact_number'].required = True