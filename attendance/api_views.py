# attendance/api_views.py

from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.db.models import Q

from .models import StudentAttendance, StaffAttendance
from .serializers import StudentAttendanceSerializer, StaffAttendanceSerializer
from rest_framework.decorators import api_view
from students.models import Student
from staff.models import Staff
from .models import Attendance, StaffAttendance
from django.utils import timezone
from django.db import models

# ---------- STUDENT ATTENDANCE ----------
class StudentAttendanceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = StudentAttendanceSerializer

    def get_queryset(self):
        queryset = StudentAttendance.objects.all()
        date = self.request.query_params.get('date')
        month = self.request.query_params.get('month')

        if date:
            queryset = queryset.filter(date=parse_date(date))
        elif month:
            queryset = queryset.filter(date__startswith=month)

        return queryset


class StudentAttendanceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StudentAttendance.objects.all()
    serializer_class = StudentAttendanceSerializer


class StudentAttendanceSummaryAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total = StudentAttendance.objects.count()
        present = StudentAttendance.objects.filter(status="Present").count()
        absent = StudentAttendance.objects.filter(status="Absent").count()
        leave = StudentAttendance.objects.filter(status="Leave").count()
        half_day = StudentAttendance.objects.filter(status="Half Day").count()

        return Response({
            "total": total,
            "present": present,
            "absent": absent,
            "leave": leave,
            "half_day": half_day
        })


# ---------- STAFF ATTENDANCE ----------
class StaffAttendanceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = StaffAttendanceSerializer

    def get_queryset(self):
        queryset = StaffAttendance.objects.all()
        date = self.request.query_params.get('date')
        month = self.request.query_params.get('month')

        if date:
            queryset = queryset.filter(date=parse_date(date))
        elif month:
            queryset = queryset.filter(date__startswith=month)

        return queryset


class StaffAttendanceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StaffAttendance.objects.all()
    serializer_class = StaffAttendanceSerializer


class StaffAttendanceSummaryAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total = StaffAttendance.objects.count()
        present = StaffAttendance.objects.filter(status="Present").count()
        absent = StaffAttendance.objects.filter(status="Absent").count()
        leave = StaffAttendance.objects.filter(status="Leave").count()
        half_day = StaffAttendance.objects.filter(status="Half Day").count()

        return Response({
            "total": total,
            "present": present,
            "absent": absent,
            "leave": leave,
            "half_day": half_day
        })
@api_view(['POST'])
def rfid_biometric_checkin(request):
    tag = request.data.get('tag')  # This could be RFID or Biometric ID

    # 1. Check student match
    student = Student.objects.filter(
        models.Q(rfid_code=tag) | models.Q(biometric_id=tag)
    ).first()

    if student:
        obj, created = Attendance.objects.get_or_create(
            student=student,
            date=timezone.now().date(),
            defaults={'status': 'present'}
        )
        return Response({"message": f"✅ Student {student.name} marked present."})

    # 2. Check staff match
    staff = Staff.objects.filter(
        models.Q(rfid_code=tag) | models.Q(biometric_id=tag)
    ).first()

    if staff:
        obj, created = StaffAttendance.objects.get_or_create(
            staff=staff,
            date=timezone.now().date(),
            defaults={'status': 'present'}
        )
        return Response({"message": f"✅ Staff {staff.full_name} marked present."})

    return Response({"error": "❌ Tag not registered for any student or staff"}, status=404)