from django.contrib import admin
from .models import Department, Designation, Staff
from django.utils.html import format_html

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')
    search_fields = ('title',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        'staff_id', 'full_name', 'staff_category', 'staff_role',
        'department', 'designation', 'contact_number', 'status', 'photo_tag','rfid_code', 'biometric_id',
    )
    list_filter = ('staff_category', 'staff_role', 'status', 'department')
    search_fields = ('full_name', 'staff_id', 'contact_number', 'email')
    readonly_fields = ('staff_id', 'photo_tag')  # auto-generated staff_id

    def photo_tag(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.photo.url)
        return "-"
    photo_tag.short_description = 'Photo'
