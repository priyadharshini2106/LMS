from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('timetable_list'), name='timetable_home'),
    path('entries/', views.timetable_list, name='timetable_list'),
    path('entries/add/', views.add_timetable_slot, name='add_timetable_slot'),
    path('entries/edit/<int:pk>/', views.edit_timetable_slot, name='edit_timetable_slot'),
    path('periods/', views.period_list, name='period_list'),
    path('periods/add/', views.add_period, name='add_period'),
    path('periods/edit/<int:pk>/', views.edit_period, name='edit_period'),
    path('generate/', views.generate_auto_timetable, name='generate_auto_timetable'),
    path('export/pdf/', views.export_timetable_pdf, name='export_timetable_pdf'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
]
