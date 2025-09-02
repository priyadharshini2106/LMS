# Fully coded admin.py for library
print('library admin.py loaded')
from django.contrib import admin
from .models import Book, BookIssue


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'total_copies', 'available_copies')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('author', 'publisher')
    ordering = ('title',)


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'issue_date', 'due_date', 'return_date', 'is_overdue_display')
    list_filter = ('issue_date', 'due_date', 'return_date')
    search_fields = ('book__title', 'student__full_name')

    def is_overdue_display(self, obj):
        return obj.is_overdue()
    is_overdue_display.short_description = 'Overdue'
    is_overdue_display.boolean = True
