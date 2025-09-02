# exams/forms.py
from django import forms
from django.forms import modelformset_factory
from django.contrib.auth import get_user_model

from students.models import ClassSection
from .models import (
    ExamMark, ExamSchedule, Term, Subject, ExamType, ExamRoom
)

User = get_user_model()


# ---------- Bulk mark row form ----------
# exams/forms.py
from django import forms
from django.forms import modelformset_factory

from .models import ExamMark, ExamSchedule


class BulkExamMarkForm(forms.ModelForm):
    """
    One row in the bulk marks table.
    We restrict the exam_schedule choices per (section, term, subject)
    and keep the row's currently selected schedule valid even if it's
    not part of the filtered queryset.
    """
    class Meta:
        model = ExamMark
        fields = ["exam_schedule", "max_marks", "marks_obtained", "remarks"]

    def __init__(self, *args, **kwargs):
        exam_schedules = kwargs.pop("exam_schedules", None)
        super().__init__(*args, **kwargs)

        qs = exam_schedules or ExamSchedule.objects.none()

        # Include the already-saved schedule if it isn't in the filtered qs,
        # so bound values don't error with "not a valid choice".
        if self.instance and self.instance.exam_schedule_id:
            qs = ExamSchedule.objects.filter(pk=self.instance.exam_schedule_id) | qs

        self.fields["exam_schedule"].queryset = qs.distinct()
        self.fields["exam_schedule"].empty_label = "— Select —"

        # Styling / UX
        sel = self.fields["exam_schedule"].widget
        sel.attrs["class"] = (sel.attrs.get("class", "") + " form-select exam-schedule-select").strip()

        for name in ("max_marks", "marks_obtained", "remarks"):
            w = self.fields[name].widget
            w.attrs["class"] = (w.attrs.get("class", "") + " form-control").strip()

        # Nice numeric inputs
        self.fields["marks_obtained"].widget.attrs.update({"step": "0.01", "min": "0"})
        self.fields["max_marks"].widget.attrs.update({"step": "0.01", "min": "0"})
        self.fields["remarks"].widget.attrs.update({"placeholder": "Optional"})


# A reusable ModelFormSet for bulk editing exam marks
BulkExamMarkFormSet = modelformset_factory(
    ExamMark,
    form=BulkExamMarkForm,
    extra=0,
    can_delete=False,
)

# exams/forms.py
from django import forms
from django.db.models.functions import Cast
from django.db.models import IntegerField
from students.models import ClassSection
from .models import Subject

class SubjectForWholeClassForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    code = forms.CharField(
        max_length=10, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    klass = forms.ChoiceField(                 # only class, not section
        choices=(),
        label="Class",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Build class choices from students.ClassSection (distinct class_name)
        try:
            classes = (ClassSection.objects
                       .annotate(cn=Cast('class_name', IntegerField()))
                       .order_by('cn')
                       .values_list('class_name', flat=True)
                       .distinct())
        except Exception:
            classes = (ClassSection.objects
                       .values_list('class_name', flat=True)
                       .distinct()
                       .order_by('class_name'))
        self.fields['klass'].choices = [(c, c) for c in classes]

    def save(self):
        """
        Create/update Subject for ALL sections of the chosen class.
        Returns (subjects, created_count).
        """
        name = self.cleaned_data['name'].strip()
        code = (self.cleaned_data.get('code') or '').strip()
        klass = self.cleaned_data['klass']

        sections = ClassSection.objects.filter(class_name=klass).order_by('section')

        subjects, created_count = [], 0
        for cs in sections:
            obj, created = Subject.objects.get_or_create(
                name=name,
                class_level=cs,           # FK to students.ClassSection
                defaults={'code': code}
            )
            if not created and code and obj.code != code:
                obj.code = code
                obj.save(update_fields=['code'])
            subjects.append(obj)
            created_count += int(created)

        return subjects, created_count


# ---------- Filters used on schedule list page ----------
class ExamScheduleFilterForm(forms.Form):
    class_level = forms.ModelChoiceField(
        queryset=ClassSection.objects.order_by('class_name', 'section'),
        label="Class Level",
        required=True
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.all().order_by('-start_date'),
        required=True
    )


# ---------- ExamSchedule admin form ----------
class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = '__all__'
        widgets = {
            "exam_date": forms.DateInput(attrs={"class": "form-control", "autocomplete": "off", "type": "date"}),
            "exam_name": forms.TextInput(attrs={"class": "form-control"}),
            "max_marks": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.5"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["class_level"].queryset = ClassSection.objects.all().order_by("class_name", "section")
        self.fields["exam_type"].queryset   = ExamType.objects.all().order_by("name")
        self.fields["term"].queryset        = Term.objects.all().order_by("-start_date")
        self.fields["room"].queryset        = ExamRoom.objects.all().order_by("building", "name")
        self.fields["invigilator"].queryset = User.objects.filter(is_staff=True).order_by("username")

        def subjects_for_section(section_id):
            try:
                cs = ClassSection.objects.get(pk=section_id)
                return Subject.objects.filter(class_level=cs).order_by("name")
            except ClassSection.DoesNotExist:
                return Subject.objects.none()

        if "class_level" in self.data and self.data.get("class_level"):
            self.fields["subject"].queryset = subjects_for_section(self.data.get("class_level"))
        elif self.instance.pk and self.instance.class_level_id:
            self.fields["subject"].queryset = subjects_for_section(self.instance.class_level_id)
        else:
            self.fields["subject"].queryset = Subject.objects.all().order_by("name")

        # cosmetic: make selects pretty
        for f in self.fields.values():
            if isinstance(f.widget, forms.Select):
                f.widget.attrs["class"] = (f.widget.attrs.get("class", "") + " form-select").strip()


# ---------- Subject form ----------
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'class_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'class_level': forms.Select(attrs={'class': 'form-control'}),
        }

# exams/forms.py
from django import forms
from students.models import ClassSection

class SubjectFilterForm(forms.Form):
    class_name = forms.ChoiceField(
        choices=[],
        required=False,
        label="Class Level",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    subject_name = forms.CharField(
        required=False,
        label="Subject Name",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Mathematics"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        classes = (ClassSection.objects
                   .values_list("class_name", flat=True)
                   .distinct()
                   .order_by("class_name"))
        self.fields["class_name"].choices = [("", "— All Classes —")] + [(c, c) for c in classes]

# ---------- Single ExamMark form ----------
class ExamMarkForm(forms.ModelForm):
    class Meta:
        model = ExamMark
        fields = ['student', 'term', 'subject', 'exam_schedule',
                  'marks_obtained', 'max_marks', 'remarks']

    def clean(self):
        cleaned = super().clean()
        mo = cleaned.get('marks_obtained')
        mm = cleaned.get('max_marks')
        if mo is not None and mm is not None:
            if mm <= 0:
                self.add_error('max_marks', 'Max marks must be greater than zero.')
            elif mo < 0:
                self.add_error('marks_obtained', 'Marks obtained cannot be negative.')
            elif mo > mm:
                self.add_error('marks_obtained', 'Marks obtained cannot exceed max marks.')
        return cleaned
