print('reports views.py loaded')

import csv
import datetime
from django.shortcuts import render
from django.http import HttpResponse
from weasyprint import HTML
from django.template.loader import render_to_string
from fees.models import FeePayment
from attendance.models import StudentAttendance, StaffAttendance


# ✅ REPORTS DASHBOARD VIEW
# def reports_index(request):
#     return render(request, 'reports/reports_dashboard.html')
# reports/views.py
# reports/views.py

from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from attendance.models import StudentAttendance, StaffAttendance
from students.models import Student
from staff.models import Staff  # Make sure this import is correct based on your app

@login_required
def reports_index(request):
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    student_attendance = StudentAttendance.objects.filter(date=selected_date)
    staff_attendance = StaffAttendance.objects.filter(date=selected_date)

    context = {
        'selected_date': selected_date,
        'student_records': student_attendance.order_by('-date')[:5],
        'total_students': Student.objects.count(),
        'total_present': student_attendance.filter(status='Present').count(),
        'total_absent': student_attendance.filter(status='Absent').count(),

        # ✅ New staff attendance data
        'total_staff': Staff.objects.count(),
        'staff_present': staff_attendance.filter(status='Present').count(),
        'staff_absent': staff_attendance.filter(status='Absent').count(),
    }

    return render(request, 'reports/reports_dashboard.html', context)



# ✅ FEES PDF REPORT
def fees_pdf_report(request):
    records = FeePayment.objects.all()
    html_string = render_to_string('reports/fees_pdf.html', {'records': records})
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename=fees_report_{datetime.date.today()}.pdf'
    return response


# ✅ FEES EXCEL REPORT
def fees_excel_report(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=fees_report_{datetime.date.today()}.csv'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Category', 'Amount', 'Date'])

    for obj in FeePayment.objects.all():
        writer.writerow([obj.student.full_name, obj.category.name, obj.amount, obj.paid_date])

    return response


# ✅ STUDENT ATTENDANCE EXCEL REPORT
def student_attendance_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=student_attendance_{datetime.date.today()}.csv'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Date', 'Status'])

    for record in StudentAttendance.objects.all():
        writer.writerow([record.student.full_name, record.date, record.status])

    return response


# ✅ STAFF ATTENDANCE EXCEL REPORT
def staff_attendance_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=staff_attendance_{datetime.date.today()}.csv'

    writer = csv.writer(response)
    writer.writerow(['Staff', 'Date', 'Status'])

    for record in StaffAttendance.objects.all():
        writer.writerow([record.staff.full_name, record.date, record.status])

    return response
