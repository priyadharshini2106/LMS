# periyanachi_erp/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('admin/', admin.site.urls), 
    path('hostel/', include('hostel.urls')),
    path('api/auth/login/', obtain_auth_token, name='api-token-auth'),     
             # ✅ API Routes
    path('api/students/', include('students.api_urls')),        # Django admin
    path('api/staff/', include('staff.api_urls')),
    path('api/attendance/', include('attendance.api_urls')),
  
    path('', include('users.urls')),              # Custom login + dashboards
    path('students/', include('students.urls')),  
    path('staff/', include('staff.urls')),        # Staff Management

    # Fees module (namespaced)
    path('fees/', include(('fees.urls', 'fees'), namespace='fees')),
    path('exams/', include(('exams.urls', 'exams'), namespace='exams')),
    path('timetable/', include('timetable.urls')),
    path('library/', include('library.urls')),
    path('certificates/', include('certificates.urls')),
    path('reports/', include('reports.urls')),
    path('events/', include('events.urls')),
    path('profile/', include('profile.urls')),
    path('attendance/', include('attendance.urls')),
    
    

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
