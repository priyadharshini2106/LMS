print('students urls.py loaded')

from django.urls import path
from . import views

urlpatterns = [
    # Student List & Home Page
    path('', views.student_list, name='student_list'),  # Loads at /students/

    # Create, Edit, Delete
    path('add/', views.add_student, name='add_student'),
    path('<int:pk>/delete/', views.delete_student, name='delete_student'),
    path('<int:pk>/edit/', views.edit_student, name='edit_student'),   # if you have it

    # Search & Export
    path('search/', views.search_student, name='search_student'),
    path('export/excel/', views.export_students_excel, name='export_students_excel'),
    path('export/pdf/', views.export_students_pdf, name='export_students_pdf'),

    path('upload/excel/', views.upload_students_excel, name='upload_students_excel'),

    path('<int:pk>/notifications/', views.student_notifications, name='student_notifications'),
    path('<int:pk>/notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),

]
