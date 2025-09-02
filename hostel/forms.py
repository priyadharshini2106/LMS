# hostel/forms.py
from decimal import Decimal
from django import forms
from django.core.validators import RegexValidator
from django.forms import inlineformset_factory
from .models import Hostel, Room, Bed, Allocation, HostelPayment, VisitorLog, Outpass, Complaint
from students.models import Student

# -------------------- Hostel --------------------
_phone_validator = RegexValidator(
    regex=r'^\+?[0-9\s\-]{7,20}$',
    message="Enter a valid phone number (digits, spaces, +, -).",
)

class HostelForm(forms.ModelForm):
    warden_contact = forms.CharField(
        required=False,
        validators=[_phone_validator],
        widget=forms.TextInput(attrs={
            'placeholder': '+91 9XXXXXXXXX',
            'inputmode': 'tel',
            'class': 'form-control'
        }),
        help_text="Optional",
    )

    class Meta:
        model = Hostel
        fields = [
            "name", "code", "capacity", "gender_policy",
            "warden_name", "warden_contact", "warden_image"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Hostel name", "class": "form-control"}),
            "code": forms.TextInput(attrs={"placeholder": "Code", "class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"min": 0, "class": "form-control"}),
            "gender_policy": forms.Select(attrs={"class": "form-select"}),
            "warden_name": forms.TextInput(attrs={"placeholder": "Warden full name", "class": "form-control"}),
        }

    def clean_warden_contact(self):
        v = (self.cleaned_data.get("warden_contact") or "").strip()
        return " ".join(v.split()) or None


# -------------------- Room & Bed --------------------
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["hostel", "room_number", "floor"]
        widgets = {
            "hostel": forms.Select(attrs={"class": "form-select"}),
            "room_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 101"}),
            "floor": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g., 1"}),
        }

BedFormSet = inlineformset_factory(
    parent_model=Room,
    model=Bed,
    fields=["bed_number", "is_available"],
    widgets={
        "bed_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., A1"}),
        "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
    },
    extra=0,          # no empty rows by default; we add via JS
    can_delete=True,  # allow removing beds
    min_num=0,
    validate_min=False,
)

# -------------------- Allocation --------------------
class AllocationForm(forms.ModelForm):
    class Meta:
        model = Allocation
        fields = ["student", "bed", "status"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "bed": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.filter(status="Active").order_by("name")
        self.fields["student"].empty_label = "— Select a student —"

        self.fields["bed"].queryset = Bed.objects.filter(is_available=True).select_related(
            "room", "room__hostel"
        ).order_by("room__hostel__name", "room__room_number", "bed_number")
        self.fields["bed"].empty_label = "— Select an available bed —"

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get("student")
        bed = cleaned.get("bed")
        if student and bed:
            if not bed.is_available:
                self.add_error("bed", "Selected bed is no longer available. Please refresh.")
            if Allocation.objects.filter(student=student, status="ACTIVE").exists():
                self.add_error("student", "This student already has an active allocation.")
        return cleaned


# -------------------- Hostel Payment --------------------
class PaymentForm(forms.ModelForm):
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = HostelPayment
        fields = ['student', 'hostel', 'amount', 'payment_date', 'method', 'receipt_no']
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "hostel": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0.01", "step": "0.01"}),
            "method": forms.Select(attrs={
                "class": "form-select",
                "choices": [
                    ('Cash', 'Cash'),
                    ('Card', 'Card'),
                    ('UPI', 'UPI'),
                    ('Online', 'Online'),
                ]
            }),
            "receipt_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.filter(status="Active").order_by("name")

    def clean_amount(self):
        amt = self.cleaned_data.get("amount")
        if amt and amt <= Decimal("0.00"):
            raise forms.ValidationError("Payment amount must be greater than 0.")
        return amt


# -------------------- Visitor --------------------
class VisitorForm(forms.ModelForm):
    class Meta:
        model = VisitorLog
        fields = [
            "hostel", "admission_number", "student_name", "student_class",
            "visitor_name", "relationship", "purpose", "visit_date", "out_time"
        ]
        widgets = {
            "hostel": forms.Select(attrs={"class": "form-select"}),
            "admission_number": forms.TextInput(attrs={"placeholder": "Enter Admission No", "class": "form-control"}),
            "student_name": forms.TextInput(attrs={"readonly": "readonly", "class": "form-control"}),
            "student_class": forms.TextInput(attrs={"readonly": "readonly", "class": "form-control"}),
            "visitor_name": forms.TextInput(attrs={"placeholder": "Visitor Name", "class": "form-control"}),
            "relationship": forms.TextInput(attrs={"placeholder": "Relationship", "class": "form-control"}),
            "purpose": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "visit_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "out_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_name"].required = False
        self.fields["student_class"].required = False
        self.fields["out_time"].required = False
        self.fields["relationship"].required = False


# -------------------- Outpass --------------------
class OutpassForm(forms.ModelForm):
    class Meta:
        model = Outpass
        fields = ['student', 'reason', 'start_date', 'end_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("End date cannot be earlier than start date.")
        return cleaned_data


#--------Complaint---------
class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['student', 'description', 'status']  # Exclude 'date_created'
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class OutpassRequestForm(forms.ModelForm):
    class Meta:
        model = Outpass
        fields = ['student', 'reason', 'start_date', 'end_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("End date cannot be earlier than start date.")
        return cleaned_data