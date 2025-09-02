# attendance/views.py
from datetime import datetime
from io import BytesIO
import json

import pandas as pd
import openpyxl
from weasyprint import HTML

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt

from .forms import StudentAttendanceForm, StaffAttendanceForm
from .models import StudentAttendance, StaffAttendance, AttendanceType, BiometricLog
from students.models import Student, ClassSection
from staff.models import Staff
from django.db import models



from .models import (
    StudentAttendance,
    StaffAttendance,
    AttendanceType,
    BiometricLog,
)
from .forms import StudentAttendanceForm, StaffAttendanceForm
from students.models import Student, ClassSection
from staff.models import Staff

# ------------------------------
# DASHBOARD VIEWS
# ------------------------------

@login_required
def attendance_dashboard(request):
    return render(request, 'attendance/attendance_home.html')

@login_required
def student_attendance_dashboard(request):
    return render(request, 'attendance/student_attendance_home.html')

@login_required
def staff_attendance_dashboard(request):
    return render(request, 'attendance/staff_attendance_home.html')


# ------------------------------
# STUDENT ATTENDANCE CRUD
# ------------------------------

@login_required
def add_student_attendance(request):
    if request.method == 'POST':
        form = StudentAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student attendance recorded successfully.')
            return redirect('student_attendance_list')
    else:
        form = StudentAttendanceForm()
    return render(request, 'attendance/student_attendance_form.html', {'form': form, 'title': 'Add Student Attendance'})

@login_required
def edit_student_attendance(request, pk):
    record = get_object_or_404(StudentAttendance, pk=pk)
    form = StudentAttendanceForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Student attendance updated successfully.')
        return redirect('student_attendance_list')
    return render(request, 'attendance/student_attendance_form.html', {'form': form, 'title': 'Edit Student Attendance'})

@login_required
def delete_student_attendance(request, pk):
    record = get_object_or_404(StudentAttendance, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Student attendance deleted successfully.')
        return redirect('student_attendance_list')
    return render(request, 'attendance/confirm_delete.html', {'record': record, 'title': 'Confirm Delete'})

@login_required
def bulk_entry_student_attendance(request):
    class_list = ClassSection.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
    section_list = ClassSection.objects.values_list('section', flat=True).distinct().order_by('section')

    selected_class = request.GET.get('class_name')
    selected_section = request.GET.get('section')
    today = timezone.now().date()

    students = Student.objects.all()
    if selected_class:
        students = students.filter(class_section__class_name=selected_class)
    if selected_section:
        students = students.filter(class_section__section=selected_section)

    students = students.order_by('roll_no')

    if request.method == 'POST':
        date = request.POST.get('date') or today
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Present')
            remarks = request.POST.get(f'remarks_{student.id}', 'Nil')
            StudentAttendance.objects.update_or_create(
                student=student, date=date,
                defaults={'status': status, 'remarks': remarks}
            )
        messages.success(request, f'Attendance recorded for {students.count()} students.')
        return redirect('student_attendance_list')

    return render(request, 'attendance/bulk_entry_student_attendance.html', {
        'students': students,
        'today': today,
        'attendance_choices': AttendanceType.choices,
        'class_list': class_list,
        'section_list': section_list,
        'selected_class': selected_class,
        'selected_section': selected_section,
    })

@login_required
def quick_mark_attendance(request):
    students = Student.objects.order_by('name')
    today = timezone.now().date()
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Absent')
            StudentAttendance.objects.update_or_create(student=student, date=today, defaults={'status': status})
        messages.success(request, 'Student attendance marked successfully.')
        return redirect('student_attendance_list')
    return render(request, 'attendance/quick_mark_student.html', {'students': students, 'today': today})

@login_required
def student_attendance_list(request):
    selected_date = request.GET.get('date', timezone.now().date())
    selected_roll_no = request.GET.get('roll_no', '').strip()
    selected_class = request.GET.get('class_name', '').strip()
    selected_section = request.GET.get('section', '').strip()

    if isinstance(selected_date, str):
        try:
            selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()

    records = StudentAttendance.objects.select_related('student').filter(date=selected_date)

    if selected_roll_no:
        records = records.filter(student__roll_no__icontains=selected_roll_no)
    if selected_class:
        records = records.filter(student__class_section__class_name__iexact=selected_class)
    if selected_section:
        records = records.filter(student__class_section__section__iexact=selected_section)

    class_list = ClassSection.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
    section_list = ClassSection.objects.values_list('section', flat=True).distinct().order_by('section')

    return render(request, 'attendance/student_attendance_list.html', {
        'records': records,
        'title': 'Student Attendance List',
        'selected_date': selected_date,
        'selected_roll_no': selected_roll_no,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'class_list': class_list,
        'section_list': section_list,
        'total_students': records.count(),
        'total_present': records.filter(status='Present').count(),
        'total_absent': records.filter(status='Absent').count(),
    })

@login_required
def upload_attendance_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            df = pd.read_excel(request.FILES['excel_file'])
            success = 0
            errors = 0
            for _, row in df.iterrows():
                try:
                    admission_number = str(row.get('Admission Number')).strip()
                    status = str(row.get('Status', 'Present')).strip()
                    remarks = str(row.get('Remarks', 'Nil')).strip()
                    date_val = row.get('Date') or timezone.now().date()
                    if isinstance(date_val, str):
                        date_val = timezone.datetime.strptime(date_val, '%Y-%m-%d').date()
                    student = Student.objects.get(admission_number=admission_number)
                    StudentAttendance.objects.update_or_create(
                        student=student, date=date_val,
                        defaults={'status': status, 'remarks': remarks}
                    )
                    success += 1
                except Exception as e:
                    errors += 1
                    messages.warning(request, f"Error: {e}")
            messages.success(request, f"Uploaded {success} records with {errors} errors.")
            return redirect('student_attendance_list')
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
    return render(request, 'attendance/upload_attendance_excel.html', {'title': 'Upload Student Attendance'})
# attendance/views.py



from .models import (
    StudentAttendance,
    StaffAttendance,
    AttendanceType,
    BiometricLog,
)

# ------------------------------
# DASHBOARD VIEWS
# ------------------------------

@login_required
def attendance_dashboard(request):
    return render(request, 'attendance/attendance_home.html')

@login_required
def student_attendance_dashboard(request):
    return render(request, 'attendance/student_attendance_home.html')

@login_required
def staff_attendance_dashboard(request):
    return render(request, 'attendance/staff_attendance_home.html')

# ------------------------------
# STUDENT ATTENDANCE CRUD & EXPORT
# ------------------------------

@login_required
def add_student_attendance(request):
    if request.method == 'POST':
        form = StudentAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student attendance recorded successfully.')
            return redirect('student_attendance_list')
    else:
        form = StudentAttendanceForm()
    return render(request, 'attendance/student_attendance_form.html', {'form': form, 'title': 'Add Student Attendance'})

@login_required
def edit_student_attendance(request, pk):
    record = get_object_or_404(StudentAttendance, pk=pk)
    form = StudentAttendanceForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Student attendance updated successfully.')
        return redirect('student_attendance_list')
    return render(request, 'attendance/student_attendance_form.html', {'form': form, 'title': 'Edit Student Attendance'})

@login_required
def delete_student_attendance(request, pk):
    record = get_object_or_404(StudentAttendance, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Student attendance deleted successfully.')
        return redirect('student_attendance_list')
    return render(request, 'attendance/confirm_delete.html', {'record': record, 'title': 'Confirm Delete'})

@login_required
def bulk_entry_student_attendance(request):
    class_list = ClassSection.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
    section_list = ClassSection.objects.values_list('section', flat=True).distinct().order_by('section')

    selected_class = request.GET.get('class_name')
    selected_section = request.GET.get('section')
    today = timezone.now().date()

    students = Student.objects.all()
    if selected_class:
        students = students.filter(class_section__class_name=selected_class)
    if selected_section:
        students = students.filter(class_section__section=selected_section)

    students = students.order_by('roll_no')

    if request.method == 'POST':
        date = request.POST.get('date') or today
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Present')
            remarks = request.POST.get(f'remarks_{student.id}', 'Nil')
            StudentAttendance.objects.update_or_create(
                student=student, date=date,
                defaults={'status': status, 'remarks': remarks}
            )
        messages.success(request, f'Attendance recorded for {students.count()} students.')
        return redirect('student_attendance_list')

    return render(request, 'attendance/bulk_entry_student_attendance.html', {
        'students': students,
        'today': today,
        'attendance_choices': AttendanceType.choices,
        'class_list': class_list,
        'section_list': section_list,
        'selected_class': selected_class,
        'selected_section': selected_section,
    })

@login_required
def quick_mark_attendance(request):
    students = Student.objects.order_by('name')
    today = timezone.now().date()
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'Absent')
            StudentAttendance.objects.update_or_create(student=student, date=today, defaults={'status': status})
        messages.success(request, 'Student attendance marked successfully.')
        return redirect('student_attendance_list')
    return render(request, 'attendance/quick_mark_student.html', {'students': students, 'today': today})

@login_required
def student_attendance_list(request):
    selected_date = request.GET.get('date', timezone.now().date())
    selected_roll_no = request.GET.get('roll_no', '').strip()
    selected_class = request.GET.get('class_name', '').strip()
    selected_section = request.GET.get('section', '').strip()

    if isinstance(selected_date, str):
        try:
            selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()

    records = StudentAttendance.objects.select_related('student').filter(date=selected_date)

    if selected_roll_no:
        records = records.filter(student__roll_no__icontains=selected_roll_no)
    if selected_class:
        records = records.filter(student__class_section__class_name__iexact=selected_class)
    if selected_section:
        records = records.filter(student__class_section__section__iexact=selected_section)

    class_list = ClassSection.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
    section_list = ClassSection.objects.values_list('section', flat=True).distinct().order_by('section')

    return render(request, 'attendance/student_attendance_list.html', {
        'records': records,
        'title': 'Student Attendance List',
        'selected_date': selected_date,
        'selected_roll_no': selected_roll_no,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'class_list': class_list,
        'section_list': section_list,
        'total_students': records.count(),
        'total_present': records.filter(status='Present').count(),
        'total_absent': records.filter(status='Absent').count(),
    })

@login_required
def upload_attendance_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            df = pd.read_excel(request.FILES['excel_file'])
            success = 0
            errors = 0
            for _, row in df.iterrows():
                try:
                    admission_number = str(row.get('Admission Number')).strip()
                    status = str(row.get('Status', 'Present')).strip()
                    remarks = str(row.get('Remarks', 'Nil')).strip()
                    date_val = row.get('Date') or timezone.now().date()
                    if isinstance(date_val, str):
                        date_val = timezone.datetime.strptime(date_val, '%Y-%m-%d').date()
                    student = Student.objects.get(admission_number=admission_number)
                    StudentAttendance.objects.update_or_create(
                        student=student, date=date_val,
                        defaults={'status': status, 'remarks': remarks}
                    )
                    success += 1
                except Exception as e:
                    errors += 1
                    messages.warning(request, f"Error: {e}")
            messages.success(request, f"Uploaded {success} records with {errors} errors.")
            return redirect('student_attendance_list')
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
    return render(request, 'attendance/upload_attendance_excel.html', {'title': 'Upload Student Attendance'})

# attendance/views.py
from .models import (
    StudentAttendance,
    StaffAttendance,
    AttendanceType,
    BiometricLog,
)
from .forms import StudentAttendanceForm, StaffAttendanceForm
from students.models import Student, ClassSection
from staff.models import Staff

# ------------------------------
# DASHBOARD VIEWS
# ------------------------------

@login_required
def attendance_dashboard(request):
    return render(request, 'attendance/attendance_home.html')

@login_required
def student_attendance_dashboard(request):
    return render(request, 'attendance/student_attendance_home.html')

@login_required
def staff_attendance_dashboard(request):
    return render(request, 'attendance/staff_attendance_home.html')

# ------------------------------
# STAFF ATTENDANCE CRUD & EXPORT
# ------------------------------

@login_required
def staff_attendance_list(request):
    attendances = StaffAttendance.objects.select_related('staff').order_by('-date')
    return render(request, 'attendance/staff_attendance_list.html', {
        'attendances': attendances,
        'title': 'Staff Attendance List'
    })

@login_required
def add_staff_attendance(request):
    if request.method == 'POST':
        form = StaffAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff attendance recorded successfully.')
            return redirect('staff_attendance_list')
    else:
        form = StaffAttendanceForm()
    return render(request, 'attendance/staff_attendance_form.html', {'form': form, 'title': 'Add Staff Attendance'})

@login_required
def edit_staff_attendance(request, pk):
    record = get_object_or_404(StaffAttendance, pk=pk)
    form = StaffAttendanceForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Staff attendance updated successfully.')
        return redirect('staff_attendance_list')
    return render(request, 'attendance/staff_attendance_form.html', {'form': form, 'title': 'Edit Staff Attendance'})

@login_required
def delete_staff_attendance(request, pk):
    record = get_object_or_404(StaffAttendance, pk=pk)
    record.delete()
    messages.success(request, "Attendance record deleted successfully.")
    return redirect('staff_attendance_list')

@login_required
def bulk_entry_staff_attendance(request):
 # """Main attendance interface: class/section based, supports remarks and date."""   
    staffs = Staff.objects.order_by('full_name')
    today = timezone.now().date()
    if request.method == 'POST':
        for staff in staffs:
            status = request.POST.get(f'status_{staff.id}', 'Absent')
            remarks = request.POST.get(f'remarks_{staff.id}', 'Nil')
            StaffAttendance.objects.update_or_create(
                staff=staff, date=today,
                defaults={'status': status, 'remarks': remarks}
            )
        messages.success(request, f'Attendance recorded for {staffs.count()} staff.')
        return redirect('staff_attendance_list')
    return render(request, 'attendance/bulk_entry_staff_attendance.html', {
        'staffs': staffs,
        'today': today,
        'status_choices': AttendanceType.choices
    })

from django.utils.safestring import mark_safe
import json

@login_required
def quick_mark_staff_attendance(request):
    """Instant attendance marking for all staff without filters."""
    staffs = Staff.objects.order_by('full_name')
    today = timezone.now().date()

    if request.method == 'POST':
        for staff in staffs:
            status = request.POST.get(f'status_{staff.id}', 'Absent')
            remarks = request.POST.get(f'remarks_{staff.id}', 'Nil')
            StaffAttendance.objects.update_or_create(
                staff=staff, date=today,
                defaults={'status': status, 'remarks': remarks}
            )
        messages.success(request, 'Staff attendance marked successfully.')
        return redirect('staff_attendance_list')

    # ✅ Prepare staff IDs as a JSON-safe string
    staff_ids = [staff.id for staff in staffs]
    staff_ids_json = mark_safe(json.dumps(staff_ids))

    return render(request, 'attendance/quick_mark_staff.html', {
        'staffs': staffs,
        'today': today,
        'status_choices': AttendanceType.choices,
        'staff_ids_json': staff_ids_json,  # 👈 add this
    })

@login_required
def staff_attendance_summary(request):
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))

    summary = StaffAttendance.objects.filter(
        date__year=year, date__month=month
    ).values(
        'staff__department'
    ).annotate(
        present=Count('id', filter=Q(status='Present')),
        absent=Count('id', filter=Q(status='Absent')),
        leave=Count('id', filter=Q(status='Leave')),
        total=Count('id')
    ).order_by('staff__department')

    return render(request, 'attendance/staff_attendance_summary.html', {
        'title': 'Staff Attendance Summary',
        'summary': summary,
        'month': month,
        'year': year
    })

@login_required
def export_staff_attendance_summary_pdf(request):
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    records = StaffAttendance.objects.filter(date__year=year, date__month=month)
    html_string = render_to_string('attendance/staff_attendance_summary_pdf.html', {
        'records': records,
        'month_param': f"{year}-{month:02}",
        'school_name': 'Periyanachi Hr. Sec. School',
        'school_address': 'Karur, Tamil Nadu - 639001'
    })
    buffer = BytesIO()
    HTML(string=html_string).write_pdf(buffer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def staff_attendance_month_summary(request):
    staffs = Staff.objects.order_by('full_name')
    staff_id = request.GET.get('staff', '')
    month_param = request.GET.get('month', '')
    records = None
    if staff_id and month_param:
        year, month = map(int, month_param.split('-'))
        records = StaffAttendance.objects.filter(
            staff_id=staff_id,
            date__year=year,
            date__month=month
        ).order_by('date')
    return render(request, 'attendance/staff_attendance_month_summary.html', {
        'title': 'Staff Attendance – Monthly Detail',
        'staffs': staffs,
        'records': records,
        'selected_staff_id': staff_id,
        'selected_month': month_param
    })

@login_required
def export_staff_month_summary_pdf(request):
    staff_id = request.GET.get('staff')
    month_param = request.GET.get('month', '')
    year, month = map(int, month_param.split('-'))
    records = StaffAttendance.objects.filter(
        staff_id=staff_id,
        date__year=year,
        date__month=month
    ).order_by('date')
    html_string = render_to_string('attendance/staff_attendance_month_summary_pdf.html', {
        'records': records,
        'month_param': month_param,
        'school_name': 'Periyanachi Hr. Sec. School',
        'school_address': 'Karur, Tamil Nadu - 639001'
    })
    buffer = BytesIO()
    HTML(string=html_string).write_pdf(buffer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def export_staff_attendance_pdf(request):
    records = StaffAttendance.objects.all()
    html_string = render_to_string('attendance/staff_attendance_pdf.html', {
        'staff_attendance': records,
        'school_name': 'Periyanachi Hr. Sec. School',
        'school_address': 'Karur, Tamil Nadu - 639001',
        'report_generated_by': request.user.username
    })
    buffer = BytesIO()
    HTML(string=html_string).write_pdf(buffer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def export_staff_attendance_excel(request):
    records = StaffAttendance.objects.all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Staff Attendance Report"
    ws.append(["Staff Name", "Date", "Status"])
    for r in records:
        ws.append([r.staff.full_name, r.date, r.status])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@login_required
def upload_staff_attendance_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            df = pd.read_excel(request.FILES['excel_file'])
            success = 0
            errors = 0

            for _, row in df.iterrows():
                try:
                    emp_id = str(row.get('Staff ID')).strip()
                    date_val = row.get('Date') or timezone.now().date()
                    status = str(row.get('Status', 'Present')).strip()
                    remarks = str(row.get('Remarks', 'Nil')).strip()

                    if isinstance(date_val, str):
                        date_val = timezone.datetime.strptime(date_val, '%Y-%m-%d').date()

                    staff = Staff.objects.get(staff_id=emp_id)

                    StaffAttendance.objects.update_or_create(
                        staff=staff,
                        date=date_val,
                        defaults={'status': status, 'remarks': remarks}
                    )
                    success += 1
                except Staff.DoesNotExist:
                    errors += 1
                    messages.warning(request, f'Staff not found: {emp_id}')
                except Exception as e:
                    errors += 1
                    messages.warning(request, f'Error processing row: {str(e)}')

            messages.success(request, f'✅ Uploaded {success} staff records. {errors} errors.')
            return redirect('staff_attendance_list')

        except Exception as e:
            messages.error(request, f'❌ Error reading file: {str(e)}')
            return redirect('upload_staff_attendance_excel')

    return render(request, 'attendance/upload_staff_attendance_excel.html', {
        'title': 'Upload Staff Attendance Excel'
    })

@login_required
def export_student_month_summary_pdf(request):
    student_id = request.GET.get('student')
    month_param = request.GET.get('month', '')
    year, month = map(int, month_param.split('-'))
    records = StudentAttendance.objects.filter(
        student_id=student_id,
        date__year=year,
        date__month=month
    ).order_by('date')

    html_string = render_to_string('attendance/student_attendance_month_summary_pdf.html', {
        'records': records,
        'month_param': month_param,
        'school_name': 'Periyanachi Hr. Sec. School',
        'school_address': 'Karur, Tamil Nadu - 639001'
    })

    buffer = BytesIO()
    HTML(string=html_string).write_pdf(buffer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
@login_required
def export_attendance_summary_pdf(request):
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    records = StudentAttendance.objects.filter(date__year=year, date__month=month)

    html_string = render_to_string('attendance/student_attendance_summary_pdf.html', {
        'records': records,
        'month_param': f"{year}-{month:02}",
        'school_name': 'Periyanachi Hr. Sec. School',
        'school_address': 'Karur, Tamil Nadu - 639001'
    })

    buffer = BytesIO()
    HTML(string=html_string).write_pdf(buffer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

from collections import defaultdict

def student_attendance_summary(request):
    selected_month = request.GET.get('month')
    summary = defaultdict(lambda: {'Present': 0, 'Absent': 0, 'Leave': 0, 'students': set()})

    month = None
    if selected_month:
        try:
            month = datetime.strptime(selected_month, '%Y-%m')
        except ValueError:
            pass

    if month:
        attendances = StudentAttendance.objects.filter(
            date__year=month.year,
            date__month=month.month
        ).select_related('student__class_section')

        for record in attendances:
            student = record.student

            # ✅ Skip students with no class_section
            if not student.class_section:
                continue

            group_key = (student.class_section.class_name, student.class_section.section)

            summary[group_key][record.status] += 1
            summary[group_key]['students'].add(student.id)

        for group in summary:
            summary[group]['total_students'] = len(summary[group]['students'])

    return render(request, 'attendance/student_attendance_summary.html', {
        'summary': summary,
        'selected_month': selected_month,
        'title': 'Class-wise Monthly Attendance Summary',
    })

def student_attendance_month_summary(request):
    from attendance.models import StudentAttendance
    from students.models import Student
    from datetime import datetime

    selected_student_id = request.GET.get('student')
    selected_month = request.GET.get('month')

    students = Student.objects.all()
    records = []

    if selected_student_id and selected_month:
        try:
            student = Student.objects.get(id=selected_student_id)
            month = datetime.strptime(selected_month, '%Y-%m')
        except (Student.DoesNotExist, ValueError):
            student = None
            month = None

        if student and month:
            records = StudentAttendance.objects.filter(
                student=student,
                date__year=month.year,
                date__month=month.month
            ).order_by('date')

    return render(request, 'attendance/student_attendance_month_summary.html', {
        'students': students,
        'selected_student_id': selected_student_id,
        'selected_month': selected_month,
        'records': records,
        'title': 'Student Attendance – Monthly Detail',
    })
@login_required
def staff_attendance_list(request):
    q = request.GET.get('q', '').strip()
    department = request.GET.get('department', '')
    role = request.GET.get('role', '')
    selected_date = request.GET.get('date', timezone.now().date())

    records = StaffAttendance.objects.select_related('staff')
    if selected_date:
        try:
            selected_date = timezone.datetime.strptime(str(selected_date), '%Y-%m-%d').date()
            records = records.filter(date=selected_date)
        except ValueError:
            pass

    if q:
        records = records.filter(models.Q(staff__full_name__icontains=q) | models.Q(staff__staff_id__icontains=q))
    if department:
        records = records.filter(staff__department=department)
    if role:
        records = records.filter(staff__staff_role=role)

    department_choices = Staff._meta.get_field('department').choices
    role_choices = Staff._meta.get_field('staff_role').choices

    return render(request, 'attendance/staff_attendance_list.html', {
        'attendances': records,
        'title': 'Staff Attendance List',
        'selected_date': selected_date,
        'q': q,
        'department': department,
        'role': role,
        'department_choices': department_choices,
        'role_choices': role_choices,
    })


@login_required
def bulk_entry_staff_attendance(request):
    department_filter = request.GET.get('department', '')
    staffs = Staff.objects.all()
    if department_filter:
        staffs = staffs.filter(department=department_filter)
    staffs = staffs.order_by('full_name')

    today = timezone.now().date()

    if request.method == 'POST':
        scan_codes = request.POST.get('scan_codes', '').split()
        for staff in staffs:
            status = 'Absent'  # Default
            remarks = 'Nil'
            if staff.rfid_code in scan_codes or staff.biometric_id in scan_codes:
                status = 'Present'
                remarks = 'Marked via scan'
            else:
                status = request.POST.get(f'status_{staff.id}', 'Absent')
                remarks = request.POST.get(f'remarks_{staff.id}', 'Nil')

            StaffAttendance.objects.update_or_create(
                staff=staff, date=today,
                defaults={'status': status, 'remarks': remarks}
            )
        messages.success(request, f'Attendance recorded for {staffs.count()} staff.')
        return redirect('staff_attendance_list')

    return render(request, 'attendance/bulk_entry_staff_attendance.html', {
        'staffs': staffs,
        'today': today,
        'status_choices': AttendanceType.choices,
        'department_choices': Staff._meta.get_field('department').choices,
        'selected_department': department_filter,
    })
from django.db.models import Q  # Make sure this is imported at the top

def _resolve_staff(code):
    """
    Resolve staff by staff_id, RFID code, or biometric_id.
    """
    return Staff.objects.filter(
        Q(staff_id=code) |
        Q(rfid_code=code) |
        Q(biometric_id=code)
    ).first()
# ------------------------------
# API: RFID/BIOMETRIC SCAN
# ------------------------------
@csrf_exempt
def staff_attendance_scan(request):
    """
    Lightweight endpoint to mark staff attendance by RFID / biometric code.
    POST JSON: { "code": "...", "timestamp": "YYYY-mm-dd HH:MM[:SS]", "status": "Present|Absent|Leave|Half Day" }
    """
    if request.method != 'POST':
        return JsonResponse({'detail': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)

    code = data.get('code')
    status = data.get('status', 'Present')
    ts = data.get('timestamp')  # optional

    staff = _resolve_staff(code)
    if not staff:
        return JsonResponse({'detail': 'Staff not found for code'}, status=404)

    # Parse timestamp
    if ts:
        try:
            ts_dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                ts_dt = datetime.strptime(ts, '%Y-%m-%d %H:%M')
            except ValueError:
                ts_dt = timezone.now()
    else:
        ts_dt = timezone.now()

    rec, created = StaffAttendance.objects.update_or_create(
        staff=staff,
        date=ts_dt.date(),
        defaults={'status': status, 'remarks': f'Scanned {code}'}
    )

    return JsonResponse({
        'detail': 'marked',
        'created': created,
        'staff': staff.full_name,
        'date': rec.date.strftime('%Y-%m-%d'),
        'status': rec.status
    }, status=200)

def staff_attendance_home(request):
    return render(request, 'attendance/staff_attendance_home.html')