# attendance/api_urls.py

from django.urls import path
from . import api_views
from .api_views import rfid_biometric_checkin

urlpatterns = [
    # STUDENT
    path('student/', api_views.StudentAttendanceListCreateAPIView.as_view(), name='student-attendance'),
    path('student/<int:pk>/', api_views.StudentAttendanceRetrieveUpdateDestroyAPIView.as_view(), name='student-attendance-detail'),
    path('student/summary/', api_views.StudentAttendanceSummaryAPIView.as_view(), name='student-attendance-summary'),

    # STAFF
    path('staff/', api_views.StaffAttendanceListCreateAPIView.as_view(), name='staff-attendance'),
    path('staff/<int:pk>/', api_views.StaffAttendanceRetrieveUpdateDestroyAPIView.as_view(), name='staff-attendance-detail'),
    path('staff/summary/', api_views.StaffAttendanceSummaryAPIView.as_view(), name='staff-attendance-summary'),

     path('rfid-biometric-checkin/', rfid_biometric_checkin, name='rfid-biometric-checkin'),
]
