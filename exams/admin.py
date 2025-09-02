from django.contrib import admin
from .models import (
    Term, ClassLevel, Subject, ExamRoom, ExamType, 
    ExamSchedule, QuestionPaper, GradeScale, ExamMark,
    MarkEntryVerification, ExamAbsence, ResultSummary,
    ResultPublication
)
from django.db.models import Count, Avg

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'exam_count')
    search_fields = ('name',)
    ordering = ('-start_date',)
    
    def exam_count(self, obj):
        return obj.examschedule_set.count()
    exam_count.short_description = 'Exams Scheduled'

@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'medium', 'subject_count')
    list_filter = ('medium',)
    search_fields = ('name',)
    
    def subject_count(self, obj):
        return obj.subject_set.count()
    subject_count.short_description = 'Subjects'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'class_level', 'exam_count')
    list_filter = ('class_level',)
    search_fields = ('name', 'code')
    
    def exam_count(self, obj):
        return obj.examschedule_set.count()
    exam_count.short_description = 'Exams'

@admin.register(ExamRoom)
class ExamRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'capacity', 'exam_count')
    list_filter = ('building',)
    search_fields = ('name',)
    
    def exam_count(self, obj):
        return obj.examschedule_set.count()
    exam_count.short_description = 'Scheduled Exams'

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'weightage', 'exam_count')
    
    def exam_count(self, obj):
        return obj.examschedule_set.count()
    exam_count.short_description = 'Exams'

class QuestionPaperInline(admin.StackedInline):
    model = QuestionPaper
    extra = 0

@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('exam_name', 'class_level', 'term', 'subject', 
                   'exam_date', 'status', 'room', 'invigilator')
    list_filter = ('term', 'class_level', 'subject', 'status')
    search_fields = ('exam_name',)
    inlines = [QuestionPaperInline]
    date_hierarchy = 'exam_date'
    list_editable = ('status',)
    actions = ['mark_as_completed', 'mark_as_published']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} exams marked as completed.")
    mark_as_completed.short_description = "Mark selected exams as completed"
    
    def mark_as_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f"{updated} exams marked as published.")
    mark_as_published.short_description = "Mark selected exams as published"

@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ('grade', 'name', 'minimum_percentage', 'description')
    ordering = ('-minimum_percentage',)

class MarkEntryVerificationInline(admin.StackedInline):
    model = MarkEntryVerification
    extra = 0

@admin.register(ExamMark)
class ExamMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'subject', 'marks_obtained', 
                   'max_marks', 'grade', 'verified')
    list_filter = ('term', 'subject', 'grade')
    search_fields = ('student__full_name', 'subject__name', 'term__name')
    ordering = ('student', 'term')
    inlines = [MarkEntryVerificationInline]
    
    def verified(self, obj):
        return hasattr(obj, 'markentryverification')
    verified.boolean = True

@admin.register(ExamAbsence)
class ExamAbsenceAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam_schedule', 'reason_short', 
                   'documented', 'approved')
    list_filter = ('documented', 'approved', 'exam_schedule__term')
    search_fields = ('student__full_name', 'reason')
    actions = ['approve_absences']
    
    def reason_short(self, obj):
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Reason'
    
    def approve_absences(self, request, queryset):
        updated = queryset.update(approved=True, approved_by=request.user)
        self.message_user(request, f"{updated} absences approved.")
    approve_absences.short_description = "Approve selected absences"

@admin.register(ResultSummary)
class ResultSummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'total_marks', 'average', 'rank')
    list_filter = ('term',)
    search_fields = ('student__full_name',)
    ordering = ('term', 'rank')

@admin.register(ResultPublication)
class ResultPublicationAdmin(admin.ModelAdmin):
    list_display = ('term', 'publish_date', 'is_published', 'published_by')
    list_filter = ('is_published',)
    actions = ['publish_results']
    
    def publish_results(self, request, queryset):
        for pub in queryset:
            pub.is_published = True
            pub.published_by = request.user
            pub.save()
            # Here you would add code to send notifications
        self.message_user(request, f"{queryset.count()} results published.")
    publish_results.short_description = "Publish selected results"