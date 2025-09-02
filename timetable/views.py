from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TimetableSlot, Period, ClassLevel, Subject
from .forms import PeriodForm, TimetableSlotForm, TimetableFilterForm
from .utils.pdf_export import generate_timetable_pdf
from staff.models import Staff

@login_required
def timetable_list(request):
    slots = TimetableSlot.objects.select_related('class_level', 'subject', 'teacher', 'period')
    filter_form = TimetableFilterForm(request.GET or None)
    if filter_form.is_valid():
        if filter_form.cleaned_data.get("class_level"):
            slots = slots.filter(class_level=filter_form.cleaned_data["class_level"])
        if filter_form.cleaned_data.get("day"):
            slots = slots.filter(day=filter_form.cleaned_data["day"])
        if filter_form.cleaned_data.get("teacher"):
            slots = slots.filter(teacher=filter_form.cleaned_data["teacher"])
    return render(request, 'timetable/timetable_list.html', {'entries': slots, 'filter_form': filter_form})

@login_required
def generate_auto_timetable(request):
    try:
        for class_level in ClassLevel.objects.all():
            periods = Period.objects.all()
            subjects = Subject.objects.filter(class_level=class_level)
            teachers = Staff.objects.filter(staff_role='TEACHER')

            if TimetableSlot.objects.filter(class_level=class_level).exists():
                continue

            subject_cycle = list(subjects)
            teacher_cycle = list(teachers)

            subject_index = 0
            teacher_index = 0

            for day, _ in TimetableSlot._meta.get_field('day').choices:
                for period in periods:
                    if not subject_cycle or not teacher_cycle:
                        continue
                    subject = subject_cycle[subject_index % len(subject_cycle)]
                    teacher = teacher_cycle[teacher_index % len(teacher_cycle)]

                    TimetableSlot.objects.create(
                        class_level=class_level,
                        day=day,
                        period=period,
                        subject=subject,
                        teacher=teacher
                    )
                    subject_index += 1
                    teacher_index += 1

        messages.success(request, "Auto timetable generated successfully.")
    except Exception as e:
        messages.error(request, f"Auto-generation failed: {e}")
    return redirect('timetable_list')

@login_required
def export_timetable_pdf(request):
    slots = TimetableSlot.objects.select_related('class_level', 'subject', 'teacher', 'period').order_by('class_level', 'day', 'period__period_number')
    return generate_timetable_pdf(request, {'entries': slots}, filename="School_Timetable.pdf")

@login_required
def period_list(request):
    periods = Period.objects.all()
    return render(request, 'timetable/period_list.html', {'periods': periods})

@login_required
def add_period(request):
    form = PeriodForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Period added.")
        return redirect('period_list')
    return render(request, 'timetable/period_form.html', {'form': form, 'title': 'Add Period'})

@login_required
def edit_period(request, pk):
    period = get_object_or_404(Period, pk=pk)
    form = PeriodForm(request.POST or None, instance=period)
    if form.is_valid():
        form.save()
        messages.success(request, "Period updated.")
        return redirect('period_list')
    return render(request, 'timetable/period_form.html', {'form': form, 'title': 'Edit Period'})

@login_required
def add_timetable_slot(request):
    form = TimetableSlotForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Slot added.")
        return redirect('timetable_list')
    return render(request, 'timetable/timetable_form.html', {'form': form, 'title': 'Add Slot'})

@login_required
def edit_timetable_slot(request, pk):
    slot = get_object_or_404(TimetableSlot, pk=pk)
    form = TimetableSlotForm(request.POST or None, instance=slot)
    if form.is_valid():
        form.save()
        messages.success(request, "Slot updated.")
        return redirect('timetable_list')
    return render(request, 'timetable/timetable_form.html', {'form': form, 'title': 'Edit Slot'})

@login_required
def student_dashboard(request):
    student_class = getattr(request.user, 'classlevel', None)
    entries = TimetableSlot.objects.filter(class_level=student_class) if student_class else []
    return render(request, 'timetable/student_dashboard.html', {'entries': entries})

@login_required
def teacher_dashboard(request):
    try:
        teacher = request.user.staff
        entries = TimetableSlot.objects.filter(teacher=teacher)
    except Staff.DoesNotExist:
        entries = []
    return render(request, 'timetable/teacher_dashboard.html', {'entries': entries})
