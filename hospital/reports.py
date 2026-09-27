from .models import VaccinationRecord, Patient, VaccinationSession
from django.db.models import Count, Q

def generate_session_report(session_id=None, start_date=None, end_date=None, sex_filter=None, status_filter=None, age_group_filter=None):
    """
    Generates dynamic session/daily summary statistics directly from database records.
    Never relies on manual totals.
    """
    records = VaccinationRecord.objects.select_related('patient', 'vaccination_session')

    if session_id:
        records = records.filter(vaccination_session_id=session_id)
    if start_date:
        records = records.filter(vaccination_date__gte=start_date)
    if end_date:
        records = records.filter(vaccination_date__lte=end_date)
    if sex_filter:
        records = records.filter(patient__sex=sex_filter)
    if status_filter:
        records = records.filter(status=status_filter)
    if age_group_filter:
        records = records.filter(age_group=age_group_filter)

    total_patients = records.count()
    
    # Sex distribution
    male_count = records.filter(patient__sex='M').count()
    female_count = records.filter(patient__sex='F').count()
    other_sex_count = records.filter(patient__sex='O').count()

    # Status distribution
    completed_count = records.filter(status='Completed').count()
    missed_count = records.filter(status='Missed').count()
    deferred_count = records.filter(status='Deferred').count()
    cancelled_count = records.filter(status='Cancelled').count()

    # Standardized Age Group breakdown based on age AT vaccination
    age_groups_def = [
        '0–6 months', '6–12 months', '1–2 years', 
        '2–3 years', '3–4 years', '4–5 years', '5+ years'
    ]
    age_group_counts = {group: records.filter(age_group=group).count() for group in age_groups_def}

    # New vs Returning patients breakdown
    patient_ids_in_records = records.values_list('patient_id', flat=True)
    new_patients_count = 0
    returning_patients_count = 0

    for pid in set(patient_ids_in_records):
        first_record = VaccinationRecord.objects.filter(patient_id=pid).order_by('vaccination_date', 'created_at').first()
        if first_record and first_record in records:
            new_patients_count += 1
        else:
            returning_patients_count += 1

    return {
        'records': records,
        'total_patients': total_patients,
        'male_count': male_count,
        'female_count': female_count,
        'other_sex_count': other_sex_count,
        'completed_count': completed_count,
        'missed_count': missed_count,
        'deferred_count': deferred_count,
        'cancelled_count': cancelled_count,
        'age_group_counts': age_group_counts,
        'new_patients_count': new_patients_count,
        'returning_patients_count': returning_patients_count,
    }
