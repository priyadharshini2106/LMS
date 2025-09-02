from rest_framework import serializers
from .models import StudentAttendance
from .models import StaffAttendance

class StudentAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAttendance
        fields = '__all__'
        read_only_fields = ['id']
class StaffAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAttendance
        fields = '__all__'
        read_only_fields = ['id']