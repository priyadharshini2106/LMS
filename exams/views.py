from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
import weasyprint
from datetime import timedelta
from django.utils.dateparse import parse_date
from .models import ClassLevel, Term, Subject, ExamSchedule, ExamType, ExamRoom, User
from django.contrib.auth import get_user_model
import itertools

from students.models import Student
from .forms import (
    BulkExamMarkForm, BulkExamMarkFormSet,
    ExamScheduleFilterForm, ExamScheduleForm, SubjectForm, ExamMarkForm
)
from .models import (
    Term, ClassLevel, Subject, ExamSchedule, 
    ExamMark, ResultSummary, ExamType,
    ExamRoom, ExamAbsence, ResultPublication, MarkEntryVerification
)

def exam_dashboard(request):
    upcoming_exams = ExamSchedule.objects.filter(
        exam_date__gte=timezone.now(),
        exam_date__lte=timezone.now() + timedelta(days=7)
    ).order_by('exam_date')[:10]

    recent_results = ResultSummary.objects.order_by('-term__start_date')[:5]
    
    # Add these counts
    exam_count = ExamSchedule.objects.count()
    marks_count = ExamMark.objects.count()
    results_count = ResultPublication.objects.filter(is_published=True).count()

    return render(request, 'exams/exam_dashboard.html', {
        'upcoming_exams': upcoming_exams,
        'recent_results': recent_results,
        'exam_count': exam_count,
        'marks_count': marks_count,
        'results_count': results_count,
    })


# exams/views.py
from django.shortcuts import render, get_object_or_404, redirect
from students.models import ClassSection

# exams/views.py
def bulk_exam_mark_entry(request, term_id, subject_id, class_level_id):
    term = get_object_or_404(Term, id=term_id)
    subject = get_object_or_404(Subject, id=subject_id)
    class_level = _resolve_class_level_from_any_id(class_level_id)

    # If your Student model links to ClassSection, adjust this to filter by section(s) for the class_level.
    students = Student.objects.filter(class_level=class_level)

    marks_qs = ExamMark.objects.filter(term=term, subject=subject, student__in=students)

    # schedules for this class + term + subject
    exam_schedules = ExamSchedule.objects.filter(
        class_level=class_level, term=term, subject=subject
    ).order_by("exam_date", "id")

    if request.method == 'POST':
        formset = BulkExamMarkFormSet(
            request.POST,
            queryset=marks_qs,
            form_kwargs={'exam_schedules': exam_schedules}  # <-- IMPORTANT
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Marks updated successfully!')
            return redirect('exams:bulk_exam_mark_entry',
                            term_id=term.id, subject_id=subject.id, class_level_id=class_level.id)
    else:
        formset = BulkExamMarkFormSet(
            queryset=marks_qs,
            form_kwargs={'exam_schedules': exam_schedules}  # <-- IMPORTANT
        )

    return render(request, 'exams/bulk_exam_mark_entry.html', {
        'term': term,
        'subject': subject,
        'class_level': class_level,
        'formset': formset
    })

# exams/views.py
from django.shortcuts import get_object_or_404
from students.models import ClassSection

def _resolve_class_level_from_any_id(level_or_section_id):
    """
    Accepts a pk that might be a ClassLevel OR a ClassSection.
    Returns a ClassLevel instance or raises Http404.
    """
    # Try as ClassLevel first (traditional, backward-compatible)
    try:
        return ClassLevel.objects.get(pk=level_or_section_id)
    except ClassLevel.DoesNotExist:
        # Try as ClassSection -> map to parent ClassLevel
        section = get_object_or_404(ClassSection, pk=level_or_section_id)
        parent_id = _parent_level_id(section)  # you already defined this helper
        return get_object_or_404(ClassLevel, pk=parent_id)

def bulk_exam_mark_entry(request, term_id, subject_id, class_level_id):
    term = get_object_or_404(Term, id=term_id)
    subject = get_object_or_404(Subject, id=subject_id)

    # ✅ Robust: works whether class_level_id is a ClassLevel id or a ClassSection id
    class_level = _resolve_class_level_from_any_id(class_level_id)

    students = Student.objects.filter(class_level=class_level)

    marks_qs = ExamMark.objects.filter(
        term=term, subject=subject, student__in=students
    )

    if not marks_qs.exists():
        ExamMark.objects.bulk_create([
            ExamMark(
                term=term,
                subject=subject,
                student=student,
                max_marks=100,
                exam_schedule=ExamSchedule.objects.filter(
                    term=term, subject=subject, class_level=class_level
                ).first()
            ) for student in students
        ])
        marks_qs = ExamMark.objects.filter(
            term=term, subject=subject, student__in=students
        )

    if request.method == 'POST':
        formset = BulkExamMarkFormSet(request.POST, queryset=marks_qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Marks updated successfully!')
            # ✅ Correct namespace
            return redirect('exams:bulk_exam_mark_entry', term_id=term.id, subject_id=subject.id, class_level_id=class_level.id)
    else:
        formset = BulkExamMarkFormSet(queryset=marks_qs)

    return render(request, 'exams/bulk_exam_mark_entry.html', {
        'term': term,
        'subject': subject,
        'class_level': class_level,
        'formset': formset
    })


# views.py
# views.py
# exams/views.py


# at top
from students.models import ClassSection

def exam_schedule_view(request):
    form = ExamScheduleFilterForm(request.GET or None)
    schedule = None

    if form.is_valid():
        section = form.cleaned_data['class_level']  # likely a ClassSection
        term = form.cleaned_data['term']

        # Map section -> parent ClassLevel (adjust attr name if yours differs)
        level = getattr(section, 'class_level', section)

        schedule = (
            ExamSchedule.objects
            .filter(term=term, class_level=level)   # use ClassLevel here
            .select_related('subject', 'room', 'invigilator', 'class_level')
            .order_by('exam_date')
        )

    return render(request, 'exams/exam_schedule.html', {
        'form': form,
        'schedule': schedule,
    })


# exams/views.py
from django.urls import reverse
from django.db import models
from .models import ClassLevel as _CL

def _parent_level_id(section):
    # Try common names
    for attr in ['class_level', 'level', 'grade', 'parent', 'standard']:
        if hasattr(section, attr) and getattr(section, attr) is not None:
            return getattr(section, attr).pk
    # Inspect fields to find FK to exams.ClassLevel
    for f in section._meta.fields:
        if isinstance(f, models.ForeignKey) and f.related_model is _CL:
            return getattr(section, f.attname)
    return None

def add_exam_schedule(request):
    if request.method == 'POST':
        form = ExamScheduleForm(request.POST)
        if form.is_valid():
            obj = form.save()
            level_id = _parent_level_id(obj.class_level)
            url = reverse('exam_schedule_view')
            if level_id:
                url = f"{url}?class_level={level_id}&term={obj.term_id}"
            messages.success(request, 'Exam Schedule created successfully.')
            return redirect(url)
    else:
        form = ExamScheduleForm()
    return render(request, 'exams/exam_schedule_form.html', {'form': form, 'title': 'Add Exam Schedule'})

def edit_exam_schedule(request, pk):
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    if request.method == 'POST':
        form = ExamScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            obj = form.save()
            level_id = _parent_level_id(obj.class_level)
            messages.success(request, 'Exam Schedule updated successfully.')
            url = reverse('exam_schedule_view')
            if level_id:
                url = f"{url}?class_level={level_id}&term={obj.term_id}"
            return redirect(url)
    else:
        form = ExamScheduleForm(instance=schedule)
    return render(request, 'exams/exam_schedule_form.html', {
        'form': form, 'title': 'Edit Exam Schedule'
    })

# exams/views.py
from .forms import SubjectFilterForm
from .models import Subject

def subject_list(request):
    qs = (Subject.objects
          .select_related('class_level')
          .order_by('class_level__class_name', 'name'))

    filter_form = SubjectFilterForm(request.GET or None)
    if filter_form.is_valid():
        class_name = filter_form.cleaned_data.get('class_name')
        subject_name = filter_form.cleaned_data.get('subject_name')

        if class_name:
            qs = qs.filter(class_level__class_name=class_name)
        if subject_name:
            qs = qs.filter(name__icontains=subject_name)

    return render(request, 'exams/subject_list.html', {
        'subjects': qs,
        'title': 'Subject List',
        'filter_form': filter_form,   # <<< pass to template
    })


def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully.')
            return redirect('subject_list')
    else:
        form = SubjectForm()

    return render(request, 'exams/subject_form.html', {
        'form': form,
        'title': 'Add Subject'
    })


def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully.')
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)

    return render(request, 'exams/subject_form.html', {
        'form': form,
        'title': 'Edit Subject'
    })


def generate_report_card(request, student_id, term_id):
    student = get_object_or_404(Student, id=student_id)
    term = get_object_or_404(Term, id=term_id)
    marks = ExamMark.objects.filter(
        student=student,
        term=term
    ).select_related('subject')

    summary = ResultSummary.objects.filter(
        student=student,
        term=term
    ).first()

    context = {
        'student': student,
        'term': term,
        'marks': marks,
        'summary': summary,
    }

    html = render_to_string('exams/report_card_template.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{student.name}_ReportCard.pdf"'
    weasyprint.HTML(string=html).write_pdf(response)
    return response

# exams/views.py
def exam_analytics(request):
    class_level_id = request.GET.get('class_level')
    term_id = request.GET.get('term')

    marks = ExamMark.objects.select_related('student','term','subject')

    if class_level_id:
        marks = marks.filter(student__class_section__class_level_id=class_level_id)  # <-- fix

    if term_id:
        marks = marks.filter(term_id=term_id)

    data = {
        'subject_stats': marks.values('subject__name').annotate(
            avg_score=Avg('marks_obtained'),
            pass_rate=Count('id', filter=Q(grade__in=['A+','A','B','C','D'])) * 100.0 / Count('id')
        ),
        'term_stats': marks.values('term__name','term__start_date').annotate(
            avg_score=Avg('marks_obtained')
        ).order_by('term__start_date'),
        'pass_percentage': (marks.filter(grade__in=['A+','A','B','C','D']).count() * 100.0 / marks.count()) if marks.exists() else 0,
        'class_average': marks.aggregate(avg=Avg('marks_obtained'))['avg'] or 0,
        'top_students': marks.values('student__name').annotate(
            average=Avg('marks_obtained')
        ).order_by('-average')[:5],
    }

    return render(request, 'exams/exam_analytics.html', {
        'data': data,
        'class_levels': ClassLevel.objects.all(),
        'terms': Term.objects.all().order_by('-start_date')
    })


def parent_view_results(request):
    if not hasattr(request.user, 'guardian'):
        return redirect('home')

    children = request.user.guardian.children.all()
    selected_child = request.GET.get('child', children.first().id if children else None)
    selected_term = request.GET.get('term')

    results = None
    marks = None
    absences = None
    grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}

    if selected_child and selected_term:
        results = ResultSummary.objects.filter(
            student_id=selected_child,
            term_id=selected_term
        ).first()

        marks = ExamMark.objects.filter(
            student_id=selected_child,
            term_id=selected_term
        ).select_related('subject')

        for mark in marks:
            grade_counts[mark.grade[0]] += 1

        absences = ExamAbsence.objects.filter(
            student_id=selected_child,
            exam_schedule__term_id=selected_term
        ).select_related('exam_schedule__subject')

    return render(request, 'exams/parent_results.html', {
        'children': children,
        'terms': Term.objects.filter(
            exammark__student__in=children
        ).distinct().order_by('-start_date'),
        'selected_child': int(selected_child) if selected_child else None,
        'selected_term': int(selected_term) if selected_term else None,
        'selected_result': results,
        'marks': marks or [],
        'absences': absences or [],
        'grade_counts': grade_counts
    })


from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages



@require_POST
def delete_exam_mark(request, pk):
    """
    Deletes an ExamMark. Works for AJAX and normal POST.
    """
    mark = get_object_or_404(ExamMark, pk=pk)
    mark.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    messages.success(request, 'Exam mark deleted.')
    return redirect('exams:exam_mark_list')



def approve_absence(request, absence_id):
    absence = get_object_or_404(ExamAbsence, pk=absence_id)
    absence.approved = True
    absence.approved_by = request.user
    absence.approval_date = timezone.now()
    absence.save()
    return redirect('parent_results')


# views.py (add near your imports)
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages

def user_is_admin(user):
    """
    Treat 'admin' role, superuser, or staff as admin.
    Adjust if your project uses a different role field name.
    """
    role = getattr(user, 'role', None)
    return (str(role).lower() == 'admin') or user.is_superuser or user.is_staff


def exam_mark_list(request):
    marks = (
        ExamMark.objects
        .select_related('student', 'term', 'subject')
        .order_by('student__name', 'student__roll_no', 'term__start_date', 'subject__name')
    )

    term_id = request.GET.get('term')
    if term_id:
        marks = marks.filter(term_id=term_id)

    # NEW: cast for safe comparison in template
    selected_term = int(term_id) if term_id and term_id.isdigit() else None

    return render(request, 'exams/exam_mark_list.html', {
        'marks': marks,
        'terms': Term.objects.all().order_by('-start_date'),
        'selected_term': selected_term,   # pass the int (or None)
        'is_admin': user_is_admin(request.user),
    })



@require_POST
def verify_mark(request, mark_id):
    """
    AJAX-friendly verify endpoint, admin-only.
    """
    if not user_is_admin(request.user):
        # For AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'message': 'Only admins can verify marks.'}, status=403)
        # For non-AJAX
        messages.error(request, 'Only admins can verify marks.')
        return redirect('exams:exam_mark_list')

    mark = get_object_or_404(ExamMark, pk=mark_id)
    MarkEntryVerification.objects.get_or_create(
        exam_mark=mark,
        defaults={'verified_by': request.user, 'verification_date': timezone.now()}
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'message': 'Mark verified.'})

    messages.success(request, 'Mark verified.')
    return redirect('exams:exam_mark_list')

# exams/views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from decimal import Decimal
import weasyprint

from students.models import Student
from .models import ExamMark, Term
from collections import defaultdict
from decimal import Decimal
from django.conf import settings
from django.db.models import Min, Max
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
import weasyprint
import os
from django.conf import settings
from urllib.parse import urljoin
# views.py

from collections import defaultdict
from decimal import Decimal

# views.py

from collections import defaultdict
from decimal import Decimal
from datetime import date

from django.conf import settings
from django.db.models import Min, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from students.models import Student
from .models import ExamMark, Term

# ✅ WeasyPrint imports (compat across versions)
try:
    from weasyprint import HTML, CSS
    from weasyprint.fonts import FontConfiguration
except Exception:
    from weasyprint import HTML, CSS
    try:
        from weasyprint.fonts import FontConfiguration
    except Exception:
        FontConfiguration = None  # fallback if not available


def _admission_no(student):
    for attr in ("admission_no", "admission_number", "admission_id", "admission"):
        val = getattr(student, attr, None)
        if val:
            return val
    return getattr(student, "roll_no", "") or ""


def _class_display(student):
    return getattr(student, "class_section", None) or getattr(student, "class_level", "") or ""


@require_GET
def student_marksheet(request, student_id):
    student = get_object_or_404(Student, pk=student_id)

    # All marks for this student (all terms)
    marks = (
        ExamMark.objects
        .filter(student=student)
        .select_related("subject", "term")
        .order_by("subject__name", "term__start_date")
    )

    # Aggregate per subject across all terms
    from collections import defaultdict
    per_subject = defaultdict(lambda: {"name": "", "obtained": Decimal("0"), "max": Decimal("0")})
    for m in marks:
        sname = m.subject.name
        per_subject[sname]["name"] = sname
        per_subject[sname]["obtained"] += (m.marks_obtained or Decimal("0"))
        per_subject[sname]["max"] += (m.max_marks or Decimal("0"))

    # Convert to list and compute % + pass/fail using 35% rule
    PASS_THRESHOLD = Decimal("35")
    subject_rows = []
    for row in per_subject.values():
        obtained = row["obtained"]
        maxm = row["max"]
        pct = (float(obtained) / float(maxm) * 100.0) if maxm else 0.0
        passed = (maxm > 0) and (Decimal(obtained) >= (PASS_THRESHOLD/Decimal("100")) * Decimal(maxm))
        subject_rows.append({
            "name": row["name"],
            "obtained": obtained,
            "max": maxm,
            "pct": pct,
            "passed": passed,
        })

    subject_rows.sort(key=lambda x: x["name"].lower())

    # Overall totals
    overall_obtained = sum((r["obtained"] for r in subject_rows), Decimal("0"))
    overall_max = sum((r["max"] for r in subject_rows), Decimal("0"))
    overall_pct = (float(overall_obtained) / float(overall_max) * 100.0) if overall_max else 0.0
    overall_pass = all(r["passed"] for r in subject_rows) if subject_rows else True

    # Academic year from terms
    year_text = ""
    years_qs = Term.objects.filter(exammark__student=student).aggregate(
        start_min=Min("start_date"), start_max=Max("start_date")
    )
    start_min = years_qs.get("start_min")
    start_max = years_qs.get("start_max")
    if start_min and start_max:
        y1, y2 = start_min.year, start_max.year
        year_text = f"{y1}–{y2}" if y1 != y2 else f"{y1}"

    # ✅ Optional signatures and labels from settings (or defaults)
    teacher_sig_url = getattr(settings, "TEACHER_SIGNATURE_URL", "")
    principal_sig_url = getattr(settings, "PRINCIPAL_SIGNATURE_URL", "")
    teacher_name = getattr(settings, "TEACHER_NAME", "Class Teacher")
    principal_name = getattr(settings, "PRINCIPAL_NAME", "Principal")
    school_name = getattr(settings, "SCHOOL_NAME", "Periyanachi Matric. Hr. Sec. School")
    school_address = getattr(
        settings,
        "SCHOOL_ADDRESS",
        "2nd Main Road, 4th Cross Street, Kalai Nagar, Madurai, Tamilnadu - 625017 | Phone: (91) 9876543210",
    )

    context = {
        "school_name": school_name,
        "school_address": school_address,

        "student": student,
        "admission_no": _admission_no(student),
        "roll_no": getattr(student, "roll_no", ""),
        "class_display": _class_display(student),
        "academic_year": year_text,

        "subject_rows": subject_rows,
        "overall_obtained": overall_obtained,
        "overall_max": overall_max,
        "overall_pct": overall_pct,
        "overall_pass": overall_pass,
        "pass_threshold": int(PASS_THRESHOLD),

        # signatures + meta
        "today": date.today(),
        "teacher_signature_url": teacher_sig_url,
        "principal_signature_url": principal_sig_url,
        "teacher_name": teacher_name,
        "principal_name": principal_name,
    }

    # HTML page (normal view)
    if request.GET.get('format') != 'pdf':
        return render(request, 'exams/student_marksheet.html', context)

    # PDF export
    html_string = render_to_string('exams/student_marksheet.html', context)
    base_url = request.build_absolute_uri('/')  # lets WeasyPrint resolve /static and /media

    css_string = '''
        @page { size: A4; margin: 1.5cm; }
        .no-print { display: none !important; }
    '''
    font_config = FontConfiguration() if FontConfiguration else None

    html = HTML(string=html_string, base_url=base_url)
    css = CSS(string=css_string, font_config=font_config) if font_config else CSS(string=css_string)
    pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config) if font_config else html.write_pdf(stylesheets=[css])

    filename = f"{student.name.replace(' ', '_')}_Report_Card.pdf"
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ExamMarkForm
import logging

logger = logging.getLogger(__name__)

# exams/views.py
from django.middleware.csrf import get_token
from students.models import ClassSection
from .models import Term

def add_exam_mark(request):
    if request.method == 'POST':
        form = ExamMarkForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('exams:exam_mark_list')
        else:
            logger.warning("ExamMarkForm invalid: %s", form.errors)
    else:
        form = ExamMarkForm()

    return render(request, 'exams/exam_mark_form.html', {
        'form': form,
        'title': 'Add Exam Mark',
        'sections': ClassSection.objects.order_by('class_name', 'section'),
        'terms': Term.objects.order_by('-start_date'),
        'csrftoken': get_token(request),
    })


def edit_exam_mark(request, pk):
    mark = get_object_or_404(ExamMark, pk=pk)
    if request.method == 'POST':
        form = ExamMarkForm(request.POST, instance=mark)
        if form.is_valid():
            form.save()
            return redirect('exams:exam_mark_list')
    else:
        form = ExamMarkForm(instance=mark)

    return render(request, 'exams/exam_mark_form.html', {
        'form': form,
        'title': 'Edit Exam Mark',
        'sections': ClassSection.objects.order_by('class_name', 'section'),
        'terms': Term.objects.order_by('-start_date'),
        'csrftoken': get_token(request),
    })

# exams/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SubjectForWholeClassForm

def add_subject_for_class(request):
    if request.method == 'POST':
        form = SubjectForWholeClassForm(request.POST)
        if form.is_valid():
            subjects, created = form.save()
            cls = form.cleaned_data['klass']
            messages.success(
                request,
                f"Subject applied to all sections of Class {cls}. "
                f"Created: {created}, total processed: {len(subjects)}."
            )
            return redirect('exams:subject_list')
    else:
        form = SubjectForWholeClassForm()

    return render(request, 'exams/subject_form.html', {
        'form': form,
        'title': 'Add Subject (entire class)',
    })


# exams/views.py
# exams/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.forms import modelformset_factory
from django.template.loader import render_to_string
from decimal import Decimal

from students.models import ClassSection, Student
from .models import ExamMark, ExamSchedule, Subject, Term
from .forms import BulkExamMarkForm

# views.py (replace your bulk_mark_table with this version)

# exams/views.py
from decimal import Decimal

from django.db import models, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from students.models import ClassSection, Student
from .forms import BulkExamMarkForm, BulkExamMarkFormSet
from .models import ClassLevel, ExamMark, ExamSchedule, Subject, Term


def _classlevel_value_for_schedule(section: ClassSection):
    """
    Return the value to use for ExamSchedule.class_level filtering.

    If ExamSchedule.class_level points to students.ClassSection, return the section.
    If it points to exams.ClassLevel, return the parent ClassLevel of this section.
    """
    cl_field = ExamSchedule._meta.get_field("class_level")
    target_model = cl_field.remote_field.model

    if target_model is ClassSection:
        return section

    if target_model is ClassLevel:
        # Find FK to ClassLevel on ClassSection (name can vary)
        parent_pk = None
        for f in section._meta.fields:
            if isinstance(f, models.ForeignKey) and f.related_model is ClassLevel:
                parent_pk = getattr(section, f.attname)
                break
        if not parent_pk:
            return None
        return get_object_or_404(ClassLevel, pk=parent_pk)

    return None


@require_http_methods(["GET", "POST"])
def bulk_mark_table(request):
    """
    Renders and saves the bulk marks table (AJAX endpoint).

    GET:
      /exams/marks/bulk/table/?class_section=<id>&term=<id>&subject=<id>
    POST:
      Same params in form-data + formset data. Returns JSON with re-rendered table.
    """
    # --- Params ---
    section_id = request.GET.get("class_section") or request.POST.get("class_section")
    term_id = request.GET.get("term") or request.POST.get("term")
    subject_id = request.GET.get("subject") or request.POST.get("subject")

    if not (section_id and term_id and subject_id):
        return HttpResponse("Missing parameters.", status=400)

    # --- Base objects ---
    section = get_object_or_404(ClassSection, pk=section_id)
    term = get_object_or_404(Term, pk=term_id)
    subject = get_object_or_404(Subject, pk=subject_id)

    # --- Students in this section ---
    students = (
        Student.objects.filter(class_section=section, status="Active")
        .order_by("roll_no", "name")
    )

    # --- Filter schedules for this (section/level, term, subject) ---
    classlevel_value = _classlevel_value_for_schedule(section)
    if classlevel_value is None:
        return HttpResponse("ExamSchedule.class_level is not configured correctly.", status=500)

    exam_schedules = (
        ExamSchedule.objects.filter(class_level=classlevel_value, term=term, subject=subject)
        .order_by("exam_date", "id")
    )

    # --- Ensure marks exist for every student in this section + term + subject ---
    existing_qs = (
        ExamMark.objects.filter(term=term, subject=subject, student__in=students)
        .select_related("student", "exam_schedule")
        .order_by("student__roll_no", "student__name")
    )
    existing_ids = set(existing_qs.values_list("student_id", flat=True))
    missing_ids = set(students.values_list("id", flat=True)) - existing_ids

    schedule_default = exam_schedules.first()
    default_max = schedule_default.max_marks if schedule_default else Decimal("100")

    if missing_ids:
        ExamMark.objects.bulk_create([
            ExamMark(
                student_id=sid,
                term=term,
                subject=subject,
                exam_schedule=schedule_default,
                max_marks=default_max,
                marks_obtained=Decimal("0"),
                remarks="",
            )
            for sid in missing_ids
        ])
        existing_qs = (
            ExamMark.objects.filter(term=term, subject=subject, student__in=students)
            .select_related("student", "exam_schedule")
            .order_by("student__roll_no", "student__name")
        )

    # --- Build the formset (pass schedules down to each row) ---
    if request.method == "POST":
        formset = BulkExamMarkFormSet(
            request.POST,
            queryset=existing_qs,
            form_kwargs={"exam_schedules": exam_schedules},
        )
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            # Re-render fresh HTML
            fresh = BulkExamMarkFormSet(
                queryset=existing_qs,
                form_kwargs={"exam_schedules": exam_schedules},
            )
            html = render(
                request,
                "exams/_bulk_mark_table.html",
                {
                    "formset": fresh,
                    "section": section,
                    "term": term,
                    "subject": subject,
                    "exam_schedules": exam_schedules,
                    "schedule": schedule_default,
                },
            ).content.decode("utf-8")
            return JsonResponse({"ok": True, "message": "Marks saved successfully.", "html": html})
        else:
            html = render(
                request,
                "exams/_bulk_mark_table.html",
                {
                    "formset": formset,
                    "section": section,
                    "term": term,
                    "subject": subject,
                    "exam_schedules": exam_schedules,
                    "schedule": schedule_default,
                },
            ).content.decode("utf-8")
            return JsonResponse({"ok": False, "message": "Please correct the errors.", "html": html}, status=400)

    # GET
    formset = BulkExamMarkFormSet(
        queryset=existing_qs,
        form_kwargs={"exam_schedules": exam_schedules},
    )
    return render(
        request,
        "exams/_bulk_mark_table.html",
        {
            "formset": formset,
            "section": section,
            "term": term,
            "subject": subject,
            "exam_schedules": exam_schedules,
            "schedule": schedule_default,
        },
    )


#bulk scheduling
User = get_user_model()

def get_next_valid_exam_date(start_date, exams_per_day, skip_weekends, exam_count):
    if exams_per_day < 1:
        exams_per_day = 1  # Prevent divide-by-zero
    day_offset = exam_count // exams_per_day
    exam_date = start_date + timedelta(days=day_offset)

    # Skip weekends if requested
    if skip_weekends:
        while exam_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            exam_date += timedelta(days=1)
    return exam_date


def bulk_schedule_exams(request):
    if request.method == 'POST':
        class_level_id = request.POST.get('class_level')
        term_id = request.POST.get('term')
        exam_type_id = request.POST.get('exam_type')
        exams_per_day_raw = request.POST.get('exams_per_day', '1')  # default to 1
        start_date_raw = request.POST.get('start_date')
        skip_weekends = request.POST.get('skip_weekends') == 'on'
        overwrite_existing = request.POST.get('overwrite_existing') == 'on'

        # Validate integer
        try:
            exams_per_day = int(exams_per_day_raw)
            if exams_per_day < 1:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Please provide a valid positive integer for 'Exams per day'.")
            return redirect('exam_schedule_view')

        # Validate date
        start_date = parse_date(start_date_raw or '')
        if not start_date:
            messages.error(request, "Please provide a valid start date.")
            return redirect('exam_schedule_view')

        # Validate foreign keys
        try:
            class_level = ClassLevel.objects.get(id=class_level_id)
            term = Term.objects.get(id=term_id)
            exam_type = ExamType.objects.get(id=exam_type_id)
        except (ClassLevel.DoesNotExist, Term.DoesNotExist, ExamType.DoesNotExist):
            messages.error(request, "Invalid class level, term, or exam type.")
            return redirect('exam_schedule_view')

        subjects = Subject.objects.filter(class_level=class_level)

        if overwrite_existing:
            ExamSchedule.objects.filter(
                class_level=class_level,
                term=term,
                exam_type=exam_type
            ).delete()

        rooms = list(ExamRoom.objects.all())
        invigilators = list(User.objects.filter(is_staff=True))
        room_cycle = itertools.cycle(rooms) if rooms else None
        invigilator_cycle = itertools.cycle(invigilators) if invigilators else None

        count = 0
        for subject in subjects:
            if ExamSchedule.objects.filter(
                class_level=class_level,
                term=term,
                subject=subject,
                exam_type=exam_type
            ).exists():
                continue

            exam_date = get_next_valid_exam_date(start_date, exams_per_day, skip_weekends, count)

            ExamSchedule.objects.create(
                class_level=class_level,
                term=term,
                exam_type=exam_type,
                exam_name=f"{exam_type.name} - {subject.name}",
                subject=subject,
                exam_date=exam_date,
                max_marks=100,
                room=next(room_cycle) if room_cycle else None,
                invigilator=next(invigilator_cycle) if invigilator_cycle else None,
                status='draft'
            )
            count += 1

        messages.success(request, f"Scheduled {count} exams successfully.")
        return redirect('exam_schedule_view')

    # GET method
    context = {
        'class_levels': ClassLevel.objects.all(),
        'terms': Term.objects.all(),
        'exam_types': ExamType.objects.all(),
    }
    return render(request, 'exams/bulk_exam_schedule_form.html', context)

# exams/views.py
# exams/views.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from students.models import ClassSection
from .models import Subject

def ajax_subjects_for_class(request):
    """
    Input  (GET): ?class_level=<section_id>   # kept for backward compatibility
    Output (JSON): [{id: <subject_id>, name: <subject_name>}, ...]
    """
    section_id = request.GET.get("class_level")
    if not section_id:
        return JsonResponse([], safe=False)

    # guard against non-numeric ids
    try:
        section_id = int(section_id)
    except (TypeError, ValueError):
        return JsonResponse([], safe=False)

    # IMPORTANT: students.ClassSection has no 'class_level' FK; do NOT select_related it
    cs = get_object_or_404(ClassSection, pk=section_id)

    # Subject.class_level points to students.ClassSection
    subjects = (
        Subject.objects
        .filter(class_level=cs)
        .values("id", "name")
        .order_by("name")
    )
    return JsonResponse(list(subjects), safe=False)

from django.http import JsonResponse
from students.models import ClassSection, Student

def ajax_students_for_section(request):
    """
    GET /exams/ajax/students/?class_section=<id>

    Returns:
      {
        "section": "12 - A",
        "students": [{"id": 1, "name": "Arun K", "roll_no": "12A01"}, ...]
      }
    """
    section_id = request.GET.get("class_section")
    if not section_id:
        return JsonResponse({"section": "", "students": []})

    try:
        section = ClassSection.objects.get(pk=int(section_id))
    except (ValueError, ClassSection.DoesNotExist):
        return JsonResponse({"section": "", "students": []})

    students = list(
        Student.objects
        .filter(class_section=section)            # add .filter(status="Active") if needed
        .values("id", "name", "roll_no")
        .order_by("roll_no", "name")
    )
    return JsonResponse({"section": str(section), "students": students})


# exams/views.py
from django.shortcuts import get_object_or_404
from django.http import Http404
from students.models import ClassSection

def _resolve_class_level_from_any_id(level_or_section_id):
    """
    Accepts a pk that might be a ClassLevel OR a ClassSection.
    Returns a ClassLevel instance or raises Http404.
    """
    # Try as ClassLevel first (backward compatible)
    try:
        return ClassLevel.objects.get(pk=level_or_section_id)
    except ClassLevel.DoesNotExist:
        pass

    # Else treat it as a ClassSection id and map to its parent ClassLevel
    section = get_object_or_404(ClassSection, pk=level_or_section_id)
    parent_pk = _parent_level_id(section)  # you already have this helper
    if not parent_pk:
        raise Http404("This section isn't linked to a ClassLevel.")
    return get_object_or_404(ClassLevel, pk=parent_pk)
