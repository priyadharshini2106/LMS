from rest_framework import generics, filters
from .models import Student
from .serializers import StudentSerializer

class StudentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Student.objects.all().order_by('-id')
    serializer_class = StudentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'name',
        'admission_number',
        'roll_no',
        'father_name',
        'mother_name',
        'rfid_tag',  # ✅ Include for quick search by card
    ]
    ordering_fields = ['name', 'admission_number', 'roll_no', 'class_section__class_name']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Optional future filter: student_type or transport_mode
        student_type = self.request.query_params.get('student_type')
        if student_type:
            queryset = queryset.filter(student_type=student_type)

        transport_mode = self.request.query_params.get('transport_mode')
        if transport_mode:
            queryset = queryset.filter(transport_mode=transport_mode)

        return queryset


class StudentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
