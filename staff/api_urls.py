from django.urls import path
from . import api_views
from django.urls import path
from .api_views import upload_staff_excel

urlpatterns = [
    path('', api_views.StaffListCreateAPIView.as_view(), name='api-staff-list-create'),
    path('<int:pk>/', api_views.StaffRetrieveUpdateDestroyAPIView.as_view(), name='api-staff-detail'),
    path('upload-staff-excel/', upload_staff_excel, name='upload-staff-excel'),
]
