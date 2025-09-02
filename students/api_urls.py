from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.StudentListCreateAPIView.as_view(), name='api-student-list'),
    path('<int:pk>/', api_views.StudentRetrieveUpdateDestroyAPIView.as_view(), name='api-student-detail'),
]
