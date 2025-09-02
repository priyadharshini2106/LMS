from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    FeeCategory, FeeStructure, StudentFeeAssignment,
    FeePayment, InstallmentPayment, FeeConcession, FeeReminder
)
from .serializers import (
    FeeCategorySerializer, FeeStructureSerializer, StudentFeeAssignmentSerializer,
    FeePaymentSerializer, InstallmentPaymentSerializer, FeeConcessionSerializer, FeeReminderSerializer
)

# Fee Category Views
class FeeCategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = FeeCategory.objects.all()
    serializer_class = FeeCategorySerializer

class FeeCategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FeeCategory.objects.all()
    serializer_class = FeeCategorySerializer

# Fee Structure Views
class FeeStructureListCreateAPIView(generics.ListCreateAPIView):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer

class FeeStructureRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer

# Student Fee Assignment Views
class StudentFeeAssignmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = StudentFeeAssignment.objects.all()
    serializer_class = StudentFeeAssignmentSerializer

class StudentFeeAssignmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StudentFeeAssignment.objects.all()
    serializer_class = StudentFeeAssignmentSerializer

# Fee Payment Views
class FeePaymentListCreateAPIView(generics.ListCreateAPIView):
    queryset = FeePayment.objects.all()
    serializer_class = FeePaymentSerializer

class FeePaymentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FeePayment.objects.all()
    serializer_class = FeePaymentSerializer

# Installment Payment Views
class InstallmentPaymentListCreateAPIView(generics.ListCreateAPIView):
    queryset = InstallmentPayment.objects.all()
    serializer_class = InstallmentPaymentSerializer

class InstallmentPaymentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InstallmentPayment.objects.all()
    serializer_class = InstallmentPaymentSerializer

# Fee Concession Views
class FeeConcessionListCreateAPIView(generics.ListCreateAPIView):
    queryset = FeeConcession.objects.all()
    serializer_class = FeeConcessionSerializer

class FeeConcessionRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FeeConcession.objects.all()
    serializer_class = FeeConcessionSerializer

# Fee Reminder Views
class FeeReminderListCreateAPIView(generics.ListCreateAPIView):
    queryset = FeeReminder.objects.all()
    serializer_class = FeeReminderSerializer

class FeeReminderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FeeReminder.objects.all()
    serializer_class = FeeReminderSerializer
