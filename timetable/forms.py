from django import forms
from .models import Period, TimetableSlot, ClassLevel, Subject
from staff.models import Staff

class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ['period_number', 'start_time', 'end_time']
        widgets = {
            'period_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

class TimetableSlotForm(forms.ModelForm):
    class Meta:
        model = TimetableSlot
        fields = ['class_level', 'day', 'period', 'subject', 'teacher']
        widgets = {
            'class_level': forms.Select(attrs={'class': 'form-select'}),
            'day': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Staff.objects.filter(staff_role='TEACHER')

class TimetableFilterForm(forms.Form):
    class_level = forms.ModelChoiceField(queryset=ClassLevel.objects.all(), required=False)
    day = forms.ChoiceField(choices=[('', 'All Days')] + TimetableSlot._meta.get_field('day').choices, required=False)
    teacher = forms.ModelChoiceField(queryset=Staff.objects.filter(staff_role='TEACHER'), required=False)
