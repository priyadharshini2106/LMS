from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    # ✅ Redirect /fees/ to the fees dashboard (home.html)
    path('', views.fees_home, name='home'),
    path('bulk-assign/', views.bulk_assign_view, name='bulk_assign'),

    # Fee Category URLs
    path('categories/', views.fee_category_list, name='fee_category_list'),
    path('categories/add/', views.add_fee_category, name='add_fee_category'),
    path('categories/edit/<int:pk>/', views.edit_fee_category, name='edit_fee_category'),

    # Fee Structure
    path('structure/', views.fee_structure_list, name='fee_structure_list'),
    path('structure/add/', views.add_fee_structure, name='add_fee_structure'),
    path('structure/edit/<int:pk>/', views.edit_fee_structure, name='edit_fee_structure'),

    # Student Fee Assignment
    path('assignments/', views.student_fee_assignment_list, name='student_fee_assignment_list'),
    path('assignments/add/', views.assign_fee_to_student, name='assign_fee_to_student'),
    path('assignments/edit/<int:pk>/', views.edit_student_fee_assignment, name='edit_student_fee_assignment'),
    path('assignments/delete/<int:pk>/', views.delete_student_fee_assignment, name='delete_student_fee_assignment'),

    # Fee Payment
    path('payments/', views.fee_payment_list, name='fee_payment_list'),
    path('payments/add/', views.add_fee_payment, name='add_fee_payment'),
    path('payments/edit/<int:pk>/', views.edit_fee_payment, name='edit_fee_payment'),

    path('fee-structure/delete/<int:pk>/', views.delete_fee_structure, name='delete_fee_structure'),
    path('fee-structure/bulk-assign/<int:pk>/', views.bulk_assign_fee, name='bulk_assign_fee'),
    
    path('reports/fee-cards/', views.fee_cards_report, name='fee_cards_report'),
    path('reports/fee-card/<int:student_id>/', views.fee_card_detail, name='fee_card_detail'),

    path("reminders/sms/", views.fees_reminder_sms, name="fees_reminder_sms"),
    ]
