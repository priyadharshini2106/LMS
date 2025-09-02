from rest_framework import serializers
from .models import (
    FeeCategory,
    FeeStructure,
    StudentFeeAssignment,
    FeePayment,
    InstallmentPayment,
    FeeConcession,
    FeeReminder
)

class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = '__all__'


class FeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = '__all__'


class StudentFeeAssignmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    fee_category = serializers.CharField(source='fee_structure.fee_category.name', read_only=True)
    
    class Meta:
        model = StudentFeeAssignment
        fields = '__all__'


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    
    class Meta:
        model = FeePayment
        fields = '__all__'


class InstallmentPaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='fee_payment.student.full_name', read_only=True)

    class Meta:
        model = InstallmentPayment
        fields = '__all__'


class FeeConcessionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = FeeConcession
        fields = '__all__'


class FeeReminderSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = FeeReminder
        fields = '__all__'
