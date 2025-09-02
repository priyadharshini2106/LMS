from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import (
    FeeCategory, 
    FeeStructure, 
    FeePayment, 
    StudentFeeAssignment, 
    InstallmentPayment, 
    FeeConcession, 
    FeeReport, 
    FeeReminder
)
from .services import FeeAssignmentService

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'fee_type', 'applicable_to', 'is_refundable', 'status')
    list_filter = ('fee_type', 'applicable_to', 'status')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'class_name', 'medium', 'fee_category', 'amount', 'due_date', 'installments')
    list_filter = ('class_name', 'medium', 'fee_category', 'academic_year')
    search_fields = ('class_name', 'fee_category__name', 'academic_year__name')
    ordering = ('class_name', 'medium')
    actions = ['bulk_assign_to_class']

    @admin.action(description='📌 Bulk assign to class')
    def bulk_assign_to_class(self, request: HttpRequest, queryset: QuerySet) -> None:
        """
        Bulk assigns the selected fee structure to all students in the same class.
        Only one fee structure can be selected at a time.
        """
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly ONE fee structure", level=messages.ERROR)
            return
        
        fee_structure = queryset.first()
        try:
            success = FeeAssignmentService.bulk_assign_by_class(
                class_name=fee_structure.class_name,
                fee_structure_id=fee_structure.id
            )
            if success is not None:
                self.message_user(
                    request,
                    f"Successfully assigned to {success} students in {fee_structure.class_name}",
                    level=messages.SUCCESS
                )
            else:
                self.message_user(request, "Bulk assignment failed", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error during bulk assignment: {str(e)}", level=messages.ERROR)

@admin.register(StudentFeeAssignment)
class StudentFeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_fee_category', 'original_amount', 'discount_amount', 'final_amount', 'paid_amount', 'balance_amount', 'is_fully_paid')
    list_filter = ('is_fully_paid',)
    search_fields = ('student__name', 'fee_structure__fee_category__name')
    ordering = ('student',)

    def get_fee_category(self, obj):
        return obj.fee_structure.fee_category.name
    get_fee_category.short_description = 'Fee Category'

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_fee_category', 'amount_paid', 'payment_date', 'payment_mode', 'receipt_no', 'processed_by')
    list_filter = ('payment_mode', 'payment_date')
    search_fields = ('student__name', 'receipt_no', 'fee_assignment__fee_structure__fee_category__name')
    ordering = ('-payment_date',)

    def get_fee_category(self, obj):
        return obj.fee_assignment.fee_structure.fee_category.name
    get_fee_category.short_description = 'Fee Category'

@admin.register(InstallmentPayment)
class InstallmentPaymentAdmin(admin.ModelAdmin):
    list_display = ('fee_payment', 'installment_number', 'installment_amount', 'due_date', 'is_paid')
    list_filter = ('is_paid', 'due_date')
    search_fields = ('fee_payment__student__name', 'installment_number')
    ordering = ('due_date',)

    def fee_payment(self, obj):
        return obj.fee_payment.receipt_no
    fee_payment.short_description = 'Fee Payment'

@admin.register(FeeConcession)
class FeeConcessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'concession_type', 'discount_percentage', 'valid_from', 'valid_until')
    list_filter = ('concession_type', 'valid_from', 'valid_until')
    search_fields = ('student__name', 'concession_type')
    ordering = ('valid_from',)

@admin.register(FeeReport)
class FeeReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_by', 'generated_on')
    list_filter = ('report_type',)
    search_fields = ('generated_by',)
    ordering = ('-generated_on',)

@admin.register(FeeReminder)
class FeeReminderAdmin(admin.ModelAdmin):
    list_display = ('student', 'reminder_type', 'message', 'send_date', 'status')
    list_filter = ('status', 'send_date')
    search_fields = ('student__name', 'message')
    ordering = ('-send_date',)