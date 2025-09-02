# attendance/urls.py
print('attendance urls.py loaded')

from django.urls import path
from . import views



urlpatterns = [
    # Dashboard
    path('', views.attendance_dashboard, name='attendance_dashboard'),
    path('student/dashboard/', views.student_attendance_dashboard, name='student_attendance_dashboard'),
    path('staff/dashboard/',  views.staff_attendance_dashboard,  name='staff_attendance_dashboard'),
    path('staff/upload-excel/', views.upload_staff_attendance_excel, name='upload_staff_attendance_excel'),
    # Student Attendance CRUD
    path('student/', views.student_attendance_list, name='student_attendance_list'),
    path('student/add/', views.add_student_attendance, name='add_student_attendance'),
    path('student/edit/<int:pk>/', views.edit_student_attendance, name='edit_student_attendance'),
    path('student/delete/<int:pk>/', views.delete_student_attendance, name='delete_student_attendance'),
    path('student/bulk/', views.bulk_entry_student_attendance, name='bulk_entry_student_attendance'),
    path('student/quick-mark/', views.quick_mark_attendance, name='quick_mark_attendance'),
    path('student/upload-excel/', views.upload_attendance_excel, name='upload_attendance_excel'),

    # Student Attendance Summary
    # path('student/summary/', views.student_attendance_summary, name='student_attendance_summary'),
    # path('student/summary/pdf/', views.export_attendance_summary_pdf, name='export_attendance_summary_pdf'),
   # urls.py
    path('student/detail/', views.student_attendance_month_summary, name='student_attendance_month_summary'),
    path('class/summary/', views.student_attendance_summary, name='student_attendance_summary'),
    path('class/summary/pdf/', views.export_attendance_summary_pdf, name='export_attendance_summary_pdf'),
 

    # Student Monthly Detail & PDF
    path('student/month-summary/', views.student_attendance_month_summary, name='student_attendance_month_summary'),
    path('student/month-summary/pdf/', views.export_attendance_summary_pdf, name='export_student_month_summary_pdf'),

    # Staff Attendance CRUD
    path('staff/', views.staff_attendance_list, name='staff_attendance_list'),
    path('staff/add/', views.add_staff_attendance, name='add_staff_attendance'),
    path('staff/edit/<int:pk>/', views.edit_staff_attendance, name='edit_staff_attendance'),
    path('staff-attendance/delete/<int:pk>/', views.delete_staff_attendance, name='delete_staff_attendance'),
    # path('staff/bulk/', views.bulk_entry_staff_attendance, name='bulk_entry_staff_attendance'),
    # path('staff/bulk/', views.bulk_entry_staff_attendance, name='bulk_staff_attendance'),
    path('staff/bulk/', views.bulk_entry_staff_attendance, name='bulk_staff_attendance'),
    path('staff/quick-mark/', views.quick_mark_staff_attendance, name='quick_mark_staff_attendance'),

    # Staff Attendance Summary
    path('staff/summary/', views.staff_attendance_summary, name='staff_attendance_summary'),
    path('staff/summary/pdf/', views.export_staff_attendance_summary_pdf, name='export_staff_attendance_summary_pdf'),

    # Staff Monthly Detail & PDF
    path('staff/month-summary/', views.staff_attendance_month_summary, name='staff_attendance_month_summary'),
    path('staff/month-summary/pdf/', views.export_staff_attendance_summary_pdf, name='export_staff_month_summary_pdf'),

    # Full Staff Reports Export
    path('staff/export/pdf/', views.export_staff_attendance_pdf, name='export_staff_attendance_pdf'),
    path('staff/export/excel/', views.export_staff_attendance_excel, name='export_staff_attendance_excel'),

    path('staff/list/', views.staff_attendance_list, name='staff_attendance_list'),
    path('staff/bulk/', views.bulk_entry_staff_attendance, name='bulk_entry_staff_attendance'),
    path('staff/quick/', views.quick_mark_staff_attendance, name='quick_mark_staff_attendance'),
    path('staff/scan/', views.staff_attendance_scan, name='staff_attendance_scan'),  # RFID API
    path('staff/upload/excel/', views.upload_staff_attendance_excel, name='upload_staff_attendance_excel'),
    path('attendance/home/', views.staff_attendance_home, name='staff_attendance_home'),
    
]
