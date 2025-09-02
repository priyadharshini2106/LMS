from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'is_active', 'posted_on')
    list_filter = ('is_active', 'event_date')
    search_fields = ('title', 'description')
    ordering = ('-event_date',)
