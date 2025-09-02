from django.urls import path
from . import views
from .views import upload_staff_excel_view

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('add/', views.add_staff, name='add_staff'),
    #path('add/<int:pk>/', views.add_staff, name='add_staff'),
    path('edit/<int:pk>/', views.edit_staff, name='edit_staff'),
    # path('delete/<int:pk>/', views.delete_staff, name='delete_staff'),
    path('delete/<int:pk>/', views.delete_staff, name='delete_staff'),
    path('export/pdf/', views.export_staff_pdf, name='export_staff_pdf'),
    path('export/excel/', views.export_staff_excel, name='export_staff_excel'),
    path('upload-staff-excel/', upload_staff_excel_view, name='upload-staff-excel'),
]
