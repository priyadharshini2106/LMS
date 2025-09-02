from rest_framework import generics
from .models import Staff
from .serializers import StaffSerializer

class StaffListCreateAPIView(generics.ListCreateAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class StaffRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
# staff/views_api.py
import pandas as pd
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import Staff
from django.contrib.auth import get_user_model

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_staff_excel(request):
    file_obj = request.FILES.get('file')

    if not file_obj:
        return Response({"error": "No file uploaded"}, status=400)

    try:
        df = pd.read_excel(file_obj)

        for _, row in df.iterrows():
            Staff.objects.create(
                staff_id=row['staff_id'],
                full_name=row['full_name'],
                gender=row['gender'],
                dob=row['dob'],
                doj=row['doj'],
                contact_number=row['contact_number'],
                email=row.get('email'),
                address=row.get('address'),
                employment_type=row['employment_type'],
                salary=row['salary'],
                status=row.get('status', 'Active'),
                remarks=row.get('remarks', ''),
                staff_category=row['staff_category'],
                staff_role=row['staff_role'],
                department=row['department'],
                designation=row['designation'],
            )

        return Response({"message": "Staff uploaded successfully."})

    except Exception as e:
        return Response({"error": str(e)}, status=500)
