from django.contrib import admin
from .models import Period, TimetableSlot, ClassLevel, Subject
from staff.models import Staff


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('period_number', 'start_time', 'end_time')
    ordering = ('period_number',)

@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ('class_level', 'day', 'period', 'subject', 'teacher')
    list_filter = ('class_level', 'day', 'subject')
    search_fields = ('class_level__name', 'teacher__full_name', 'subject__name')
    ordering = ('class_level', 'day', 'period')

@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'medium')
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_level', 'is_special')
    list_filter = ('class_level', 'is_special')

