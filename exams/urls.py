# exams/urls.py
from django.urls import path
from . import views

app_name = "exams" 

urlpatterns = [
    path('', views.exam_dashboard, name='exams_dashboard'),

    # 📆 Exam Schedule
    path('schedule/', views.exam_schedule_view, name='exam_schedule_view'),
    path('schedule/add/', views.add_exam_schedule, name='add_exam_schedule'),
    path('schedule/edit/<int:pk>/', views.edit_exam_schedule, name='edit_exam_schedule'),
    path('exam-schedule/bulk-create/', views.bulk_schedule_exams, name='bulk_exam_schedule'),
    path("ajax/subjects-for-class/", views.ajax_subjects_for_class, name="ajax_subjects_for_class"),

    # 📚 Subjects
    path('subject/', views.subject_list, name='subject_list'),
    path('subject/add/', views.add_subject, name='add_subject'),
    path('subject/edit/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('subjects/add-for-class/', views.add_subject_for_class, name='subject_add_for_class'),

    # 🧾 Bulk Marks Entry
   # exams/urls.py
    path(
    'marks/bulk/<int:term_id>/<int:subject_id>/<int:class_level_id>/',
    views.bulk_exam_mark_entry,
    name='bulk_exam_mark_entry',
    ),


    # 📋 Report Card
    path('report-card/<int:student_id>/<int:term_id>/', 
         views.generate_report_card, name='generate_report_card'),

    # 📝 Exam Marks
    path('marks/', views.exam_mark_list, name='exam_mark_list'),
    path('marks/add/', views.add_exam_mark, name='add_exam_mark'),
    path('marks/<int:pk>/edit/', views.edit_exam_mark, name='edit_exam_mark'),
    path('marks/<int:mark_id>/verify/', views.verify_mark, name='verify_exam_mark'),
    path('marks/<int:pk>/delete/', views.delete_exam_mark, name='delete_exam_mark'),
    path('marksheet/<int:student_id>/', views.student_marksheet, name='student_marksheet'),
    path(
        "marks/bulk/<int:term_id>/<int:subject_id>/<int:section_id>/",
        views.bulk_exam_mark_entry,
        name="bulk_exam_mark_entry",
    ),
    path("marks/bulk/table/", views.bulk_mark_table, name="bulk_mark_table"),
    path("ajax/subjects/", views.ajax_subjects_for_class, name="ajax_subjects_for_class"),
    path("ajax/students/", views.ajax_students_for_section, name="ajax_students_for_section"),


    # 📊 Analytics
    path('analytics/', views.exam_analytics, name='exam_analytics'),
    
    # 👪 Parent Results
    path('parent-results/', views.parent_view_results, name='parent_results'),

    path('exam-schedule/bulk-create/', views.bulk_schedule_exams, name='bulk_exam_schedule'),
]