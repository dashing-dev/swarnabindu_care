from .models import AuditLog, Patient
from django.db.models import Q

def log_audit_event(user, action, object_type, object_id, description):
    """Centralized audit logger."""
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id else '',
        description=description
    )

def detect_duplicate_patients(child_name, guardian_name, phone_number, dob_ad):
    """
    Duplicate Detection Logic.
    Checks combinations:
    - name + DOB
    - guardian + phone
    - name + guardian
    - phone + DOB
    Returns list of potential matching Patient instances.
    """
    query = Q()
    if child_name and dob_ad:
        query |= Q(child_name__iexact=child_name.strip(), date_of_birth=dob_ad)
    if guardian_name and phone_number:
        query |= Q(guardian_name__iexact=guardian_name.strip(), phone_number=phone_number.strip())
    if child_name and guardian_name:
        query |= Q(child_name__iexact=child_name.strip(), guardian_name__iexact=guardian_name.strip())
    if phone_number and dob_ad:
        query |= Q(phone_number=phone_number.strip(), date_of_birth=dob_ad)

    if not query:
        return Patient.objects.none()

    return Patient.objects.filter(query).distinct()
