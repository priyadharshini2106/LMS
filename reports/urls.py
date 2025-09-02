# Fully coded urls.py for reports
print('reports urls.py loaded')
from django.urls import path
from . import views
from reports import views as report_views

urlpatterns = [
    # path('reports/', report_views.reports_index, name='reports_index'),
    path('', report_views.reports_index, name='reports_index'),
    path('fees/pdf/', views.fees_pdf_report, name='fees_pdf_report'),
    path('fees/excel/', views.fees_excel_report, name='fees_excel_report'),
    path('attendance/student/excel/', views.student_attendance_excel, name='student_attendance_excel'),
    path('attendance/staff/excel/', views.staff_attendance_excel, name='staff_attendance_excel'),
]
