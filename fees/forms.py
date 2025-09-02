from django import forms
from .models import FeeCategory, FeeStructure, StudentFeeAssignment, FeePayment, InstallmentPayment, FeeConcession, FeeReport, FeeReminder

# Fee Category Form
from django import forms
from .models import (
    FeeCategory, FeeStructure,
    StudentFeeAssignment, FeePayment, InstallmentPayment, FeeConcession, FeeReport, FeeReminder
)

class DateInput(forms.DateInput):
    input_type = 'date'

# Fee Category Form
# forms.py
# forms.py
from django import forms
from .models import FeeCategory
from students.models import ClassSection

class FeeCategoryForm(forms.ModelForm):
    applicable_to = forms.ChoiceField(choices=(), required=True)

    class Meta:
        model = FeeCategory
        fields = ['name', 'description', 'fee_type', 'applicable_to', 'is_refundable', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        static_choices = list(FeeCategory.APPLICABLE_TO)
        section_qs = ClassSection.objects.order_by('class_name', 'section')
        section_choices = [(f"sec:{cs.pk}", f"{cs.class_name}-{cs.section}") for cs in section_qs]

        # group into optgroups
        grouped = [
            ("General", static_choices),
            ("Class Sections", section_choices),
        ]

        # if editing, ensure the current value is present even if the section was deleted
        current_val = None
        if self.is_bound:
            current_val = self.data.get(self.add_prefix('applicable_to')) or None
        elif self.instance and self.instance.pk:
            current_val = self.instance.applicable_to

        all_values = {v for grp, items in grouped for (v, _) in items}
        if current_val and current_val not in all_values:
            label = current_val
            if str(current_val).startswith("sec:"):
                try:
                    pk = int(str(current_val).split(":", 1)[1])
                    cs = ClassSection.objects.filter(pk=pk).first()
                    if cs:
                        label = f"{cs.class_name}-{cs.section}"
                except ValueError:
                    pass
            grouped.append(("Current", [(current_val, f"{label} (current)")]))
            # Note: this only keeps the form from erroring when old data points to a missing section.

        self.fields['applicable_to'].choices = grouped

    def clean_applicable_to(self):
        val = self.cleaned_data['applicable_to']
        if val.startswith('sec:'):
            try:
                pk = int(val.split(':', 1)[1])
            except ValueError:
                raise forms.ValidationError("Invalid class/section choice.")
            if not ClassSection.objects.filter(pk=pk).exists():
                raise forms.ValidationError("Selected class/section not found.")
        return val

from django import forms
from .models import FeeStructure, FeeCategory

class DateInput(forms.DateInput):
    input_type = 'date'

class FeeStructureForm(forms.ModelForm):
    # This is the "choices" for Fee Category
    fee_category = forms.ModelChoiceField(
        queryset=FeeCategory.objects.filter(status=True).order_by('name'),
        required=True,
        empty_label="— Select fee category —",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Fee Category",
    )

    class Meta:
        model = FeeStructure
        fields = [
            'academic_year', 'class_name', 'medium', 'fee_category',
            'amount', 'due_date', 'installments',
            'is_hostel_related', 'is_transport_related'
        ]
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control'}),
            'medium': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'due_date': DateInput(attrs={'class': 'form-control'}),
            'installments': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def clean_class_name(self):
        return (self.cleaned_data.get('class_name') or '').strip()

# Student Fee Assignment Form
# forms.py
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from .models import StudentFeeAssignment

class StudentFeeAssignmentForm(forms.ModelForm):
    class Meta:
        model = StudentFeeAssignment
        fields = [
            'student', 'fee_structure',
            'original_amount', 'discount_amount', 'final_amount',
            'paid_amount', 'is_fully_paid'
        ]
        widgets = {
            'original_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'inputmode': 'decimal', 'class': 'form-control'}),
            'discount_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'inputmode': 'decimal', 'class': 'form-control'}),
            'final_amount':    forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'paid_amount':     forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'inputmode': 'decimal', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        orig = cleaned.get('original_amount') or Decimal('0')
        disc = cleaned.get('discount_amount') or Decimal('0')
        paid = cleaned.get('paid_amount') or Decimal('0')

        final_amount = orig - disc
        if final_amount < 0:
            raise ValidationError("Discount cannot exceed the Original Amount.")
        cleaned['final_amount'] = final_amount  # enforce on server

        if paid > final_amount:
            self.add_error('paid_amount', "Paid Amount cannot exceed Final Amount.")
        return cleaned

# Fee Payment Form
# fees/forms.py
# forms.py
# forms.py
from decimal import Decimal
from django import forms
from django.db.models import Sum
from datetime import date
from .models import FeePayment

class FeePaymentForm(forms.ModelForm):
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        initial=date.today,
    )

    class Meta:
        model = FeePayment
        exclude = ('receipt_no',)

    def clean(self):
        cleaned = super().clean()
        fa = cleaned.get('fee_assignment')
        amt = cleaned.get('amount_paid')
        student = cleaned.get('student')

        if not fa or amt is None:
            return cleaned

        # 1) Ensure the assignment belongs to the selected student
        fa_student_id = getattr(fa, 'student_id', None)
        if student and fa_student_id and fa_student_id != student.id:
            self.add_error('fee_assignment', 'Selected fee assignment does not belong to the chosen student.')
            return cleaned

        # 2) Compute already-paid total (excluding this instance on edit)
        already_paid = (
            FeePayment.objects
            .filter(fee_assignment=fa)
            .exclude(pk=self.instance.pk)
            .aggregate(s=Sum('amount_paid'))['s'] or Decimal('0')
        )

        # 3) Determine the final/total amount on the assignment
        #    (use whatever field your StudentFeeAssignment exposes)
        final_amount = (
            getattr(fa, 'final_amount', None) or
            getattr(fa, 'total_final_amount', None) or
            getattr(fa, 'amount', None)
        )

        if final_amount is not None:
            outstanding = Decimal(final_amount) - Decimal(already_paid)
            if Decimal(amt) > outstanding:
                self.add_error('amount_paid', f'Amount exceeds outstanding ₹{outstanding:.2f}.')
        # If final_amount is None, skip — but ideally add that field on the model.

        return cleaned

    def clean_payment_date(self):
        from datetime import date
        d = self.cleaned_data.get('payment_date')
        return d or date.today()
    
    # models.py (inside FeePayment.save)
from django.utils import timezone

def save(self, *args, **kwargs):
    is_new = self._state.adding

    if not self.payment_date:
        self.payment_date = timezone.localdate()

    if not self.receipt_no:
        last = FeePayment.objects.order_by('-id').first()
        if last and last.receipt_no and last.receipt_no.startswith("REC"):
            try:
                last_num = int(last.receipt_no.replace("REC", ""))  # e.g. REC007 -> 7
                self.receipt_no = f"REC{last_num + 1:03d}"
            except ValueError:
                self.receipt_no = "REC001"
        else:
            self.receipt_no = "REC001"

    super().save(*args, **kwargs)


# Installment Payment Form
class InstallmentPaymentForm(forms.ModelForm):
    class Meta:
        model = InstallmentPayment
        fields = ['fee_payment', 'installment_number', 'installment_amount', 'due_date', 'is_paid']

# Fee Concession Form
class FeeConcessionForm(forms.ModelForm):
    class Meta:
        model = FeeConcession
        fields = ['student', 'concession_type', 'discount_percentage', 'valid_from', 'valid_until']

# Fee Report Form
class FeeReportForm(forms.ModelForm):
    class Meta:
        model = FeeReport
        fields = ['report_type', 'generated_by']

# Fee Reminder Form
class FeeReminderForm(forms.ModelForm):
    class Meta:
        model = FeeReminder
        fields = ['student', 'reminder_type', 'message', 'send_date', 'status']
