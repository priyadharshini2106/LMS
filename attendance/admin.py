# Fully coded admin.py for attendance
print('attendance admin.py loaded')
from django.contrib import admin
from .models import StudentAttendance, StaffAttendance, BiometricLog


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'remarks')
    list_filter = ('status', 'date')
    search_fields = ('student__full_name', 'remarks')
    ordering = ('-date',)


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'status', 'remarks')
    list_filter = ('status', 'date')
    search_fields = ('staff__full_name', 'remarks')
    ordering = ('-date',)


@admin.register(BiometricLog)
class BiometricLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'device_id', 'staff', 'student', 'log_type')
    list_filter = ('device_id', 'log_type')
    search_fields = ('device_id', 'staff__full_name', 'student__full_name')
    ordering = ('-timestamp',)
