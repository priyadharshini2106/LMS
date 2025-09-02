# fees/services.py
from django.db import transaction
from django.db.models import Q
from students.models import Student 
from .models import FeeStructure, StudentFeeAssignment

class FeeAssignmentService:
    
    @classmethod
    def bulk_assign_by_class(cls, class_name, fee_structure_id):
        """
        Smart bulk assignment with auto-filtering by:
        - Class name
        - Hosteller/day scholar status
        - Transport users
        """
        try:
            fee_structure = FeeStructure.objects.get(id=fee_structure_id)
        except FeeStructure.DoesNotExist:
            raise ValueError("Invalid fee structure ID")

        # Base query - all students in the class
        base_query = Q(class_section__class_name=class_name)
        
        # Add category-specific filters
        if fee_structure.fee_category.applicable_to == 'hosteller':
            base_query &= Q(student_category='hosteller')
        elif fee_structure.fee_category.applicable_to == 'transport_user':
            base_query &= Q(transport_mode__in=['school_bus', 'private_bus'])
        
        students = Student.objects.filter(base_query)
        success_count = 0

        with transaction.atomic():
            for student in students:
                try:
                    StudentFeeAssignment.objects.update_or_create(
                        student=student,
                        fee_structure=fee_structure,
                        defaults={
                            'original_amount': fee_structure.amount,
                            'final_amount': fee_structure.amount,
                            'paid_amount': 0,
                            'is_fully_paid': False
                        }
                    )
                    success_count += 1
                except Exception as e:
                    # Log error but continue with other students
                    continue
        
        return success_count
    
import logging
logger = logging.getLogger(__name__)

def send_sms(phone_number: str, message: str) -> bool:
    """
    Replace this stub with your real SMS gateway integration.
    Return True on success, False on failure.
    """
    phone_number = (phone_number or "").strip()
    if not phone_number:
        logger.warning("No phone number; skipping SMS.")
        return False

    # Example: Twilio (configure settings first)
    # from twilio.rest import Client
    # from django.conf import settings
    # client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    # client.messages.create(
    #     to=phone_number,
    #     from_=settings.TWILIO_FROM,
    #     body=message
    # )

    logger.info(f"[SMS-DRYRUN] -> {phone_number}: {message}")
    return True
