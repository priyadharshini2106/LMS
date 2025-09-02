# Fully coded urls.py for certificates
print('certificates urls.py loaded')
from django.urls import path
from . import views

urlpatterns = [
    path('bonafide/<int:student_id>/', views.generate_bonafide_certificate, name='generate_bonafide_certificate'),
    path('transfer/<int:student_id>/', views.generate_transfer_certificate, name='generate_transfer_certificate'),
]
