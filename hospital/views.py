from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User, Group

from .models import (
    Patient, VaccinationSession, VaccinationRecord, 
    SessionDateAudit, AuditLog, HospitalSetting, BackupRecord
)
from .forms import (
    PatientForm, VaccinationSessionForm, SessionDateChangeForm, 
    VaccinationRecordForm, HospitalSettingForm
)
from .nepali_date import ad_to_bs, format_bs_date, calculate_exact_age, parse_bs_string
from .permissions import require_role, get_user_role, ROLE_ADMIN, ROLE_OPERATOR, ROLE_READONLY
from .services import log_audit_event, detect_duplicate_patients
from .reports import generate_session_report

import datetime

def global_hospital_context(request):
    """Context processor providing hospital settings and today's BS date."""
    today_ad = timezone.now().date()
    setting = HospitalSetting.get_settings()
    user_role = get_user_role(request.user) if request.user.is_authenticated else None
    return {
        'hospital_setting': setting,
        'today_ad': today_ad,
        'today_bs': format_bs_date(today_ad),
        'user_role': user_role,
    }

@login_required
def dashboard_view(request):
    today = timezone.now().date()
    today_session = VaccinationSession.objects.filter(session_date=today).first()
    
    total_patients = Patient.objects.count()
    today_vaccinations = VaccinationRecord.objects.filter(vaccination_date=today).count()
    completed_today = VaccinationRecord.objects.filter(vaccination_date=today, status='Completed').count()
    upcoming_sessions = VaccinationSession.objects.filter(session_date__gte=today).order_by('session_date')[:5]

    context = {
        'today_session': today_session,
        'total_patients': total_patients,
        'today_vaccinations': today_vaccinations,
        'completed_today': completed_today,
        'upcoming_sessions': upcoming_sessions,
    }
    return render(request, 'dashboard.html', context)

# ------------------------------------------------------------------------------
# PATIENT MANAGEMENT
# ------------------------------------------------------------------------------

@login_required
def patient_list_view(request):
    query = request.GET.get('q', '').strip()
    patients_qs = Patient.objects.all()

    if query:
        # Search by patient ID, child name, nepali name, guardian name, phone number, or DOB
        parsed_date = parse_bs_string(query)
        date_q = models.Q(date_of_birth=parsed_date) if parsed_date else models.Q()

        patients_qs = patients_qs.filter(
            models.Q(patient_id__icontains=query) |
            models.Q(child_name__icontains=query) |
            models.Q(nepali_name__icontains=query) |
            models.Q(guardian_name__icontains=query) |
            models.Q(phone_number__icontains=query) |
            date_q
        ).distinct()

    paginator = Paginator(patients_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'patients/list.html', {'page_obj': page_obj, 'query': query})

@login_required
@require_role([ROLE_ADMIN, ROLE_OPERATOR])
def patient_register_view(request):
    confirm_duplicate = request.POST.get('confirm_duplicate') == '1'
    duplicates = []

    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            child_name = form.cleaned_data['child_name']
            guardian_name = form.cleaned_data['guardian_name']
            phone_number = form.cleaned_data['phone_number']
            dob_ad = form.cleaned_data['dob_bs_input']

            # Check potential duplicates unless staff overrides with confirm
            possible_dups = detect_duplicate_patients(child_name, guardian_name, phone_number, dob_ad)
            if possible_dups.exists() and not confirm_duplicate:
                duplicates = possible_dups
                messages.warning(
                    request, 
                    "POSSIBLE DUPLICATE WARNING: Similar patient record(s) already exist. Please review below before proceeding."
                )
            else:
                with transaction.atomic():
                    patient = form.save()
                    log_audit_event(
                        request.user, 'PATIENT_CREATED', 'Patient', 
                        patient.patient_id, f"Registered patient {patient.child_name} (ID: {patient.patient_id})"
                    )
                    messages.success(request, f"Patient registered successfully! Generated Patient ID: {patient.patient_id}")
                    return redirect('patient_detail', patient_id=patient.patient_id)
    else:
        form = PatientForm()

    return render(request, 'patients/register.html', {
        'form': form, 
        'duplicates': duplicates
    })

@login_required
def patient_detail_view(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    vaccinations = patient.vaccinations.select_related('vaccination_session', 'next_vaccination_session', 'operator').all()
    
    # Check next upcoming session
    latest_record = vaccinations.first()
    next_session = latest_record.next_vaccination_session if latest_record else None

    return render(request, 'patients/detail.html', {
        'patient': patient,
        'vaccinations': vaccinations,
        'next_session': next_session,
    })

@login_required
def patient_print_history_view(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    vaccinations = patient.vaccinations.select_related('vaccination_session', 'operator').order_by('vaccination_date')
    
    return render(request, 'patients/print_history.html', {
        'patient': patient,
        'vaccinations': vaccinations,
        'printed_at': timezone.now()
    })

# ------------------------------------------------------------------------------
# VACCINATION WORKFLOW
# ------------------------------------------------------------------------------

@login_required
@require_role([ROLE_ADMIN, ROLE_OPERATOR])
def vaccination_record_view(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    session_id = request.GET.get('session_id')
    selected_session = None
    if session_id:
        selected_session = get_object_or_404(VaccinationSession, id=session_id)

    if request.method == 'POST':
        form = VaccinationRecordForm(request.POST, patient=patient)
        if form.is_valid():
            with transaction.atomic():
                record = form.save(commit=False)
                record.patient = patient
                record.operator = request.user
                record.vaccination_date = record.vaccination_session.session_date
                record.save()

                log_audit_event(
                    request.user, 'VACCINATION_RECORDED', 'VaccinationRecord',
                    record.id, f"Recorded vaccination for patient {patient.patient_id} in session {record.vaccination_session.program_name}"
                )
                messages.success(request, f"Vaccination recorded successfully for Patient {patient.patient_id}!")
                return redirect('patient_detail', patient_id=patient.patient_id)
    else:
        initial_data = {}
        if selected_session:
            initial_data['vaccination_session'] = selected_session
        form = VaccinationRecordForm(patient=patient, initial=initial_data)

    # Pre-calculate age on today / selected session date
    ref_date = selected_session.session_date if selected_session else timezone.now().date()
    calculated_age = calculate_exact_age(patient.date_of_birth, ref_date)

    return render(request, 'vaccination/record.html', {
        'patient': patient,
        'form': form,
        'calculated_age': calculated_age,
        'selected_session': selected_session
    })

@login_required
def today_program_view(request):
    today = timezone.now().date()
    sessions = VaccinationSession.objects.filter(session_date=today)
    active_session = sessions.first()

    today_records = []
    if active_session:
        today_records = VaccinationRecord.objects.filter(vaccination_session=active_session).select_related('patient')

    return render(request, 'vaccination/today.html', {
        'sessions': sessions,
        'active_session': active_session,
        'today_records': today_records,
    })

# ------------------------------------------------------------------------------
# VACCINATION SESSIONS MANAGEMENT
# ------------------------------------------------------------------------------

@login_required
def session_list_view(request):
    sessions = VaccinationSession.objects.all().order_by('-session_date')
    return render(request, 'sessions/list.html', {'sessions': sessions})

@login_required
@require_role([ROLE_ADMIN])
def session_create_view(request):
    if request.method == 'POST':
        form = VaccinationSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()

            log_audit_event(
                request.user, 'SESSION_CREATED', 'VaccinationSession',
                session.id, f"Created session {session.program_name} on BS date {session.session_date_bs}"
            )
            messages.success(request, f"Vaccination session '{session.program_name}' created successfully.")
            return redirect('session_list')
    else:
        form = VaccinationSessionForm()

    return render(request, 'sessions/create_edit.html', {'form': form, 'title': 'Create New Vaccination Session'})

@login_required
@require_role([ROLE_ADMIN])
def session_edit_date_view(request, session_id):
    session = get_object_or_404(VaccinationSession, id=session_id)
    associated_records_count = session.records.count()

    if request.method == 'POST':
        form = SessionDateChangeForm(request.POST)
        if form.is_valid():
            new_date = form.cleaned_data['new_date_bs']
            reason = form.cleaned_data['reason']
            old_date = session.session_date

            with transaction.atomic():
                session.session_date = new_date
                if session.status == 'Scheduled':
                    session.status = 'Postponed'
                session.save()

                # Audit trail
                SessionDateAudit.objects.create(
                    session=session,
                    old_date=old_date,
                    new_date=new_date,
                    reason=reason,
                    changed_by=request.user
                )

                log_audit_event(
                    request.user, 'SESSION_DATE_CHANGED', 'VaccinationSession',
                    session.id, f"Session {session.program_name} rescheduled from {format_bs_date(old_date)} to {format_bs_date(new_date)}. Reason: {reason}"
                )

                messages.success(request, f"Session date updated to {format_bs_date(new_date)}. Change recorded in audit log.")
                return redirect('session_list')
    else:
        form = SessionDateChangeForm()

    return render(request, 'sessions/change_date.html', {
        'session': session,
        'form': form,
        'associated_records_count': associated_records_count
    })

# ------------------------------------------------------------------------------
# REPORTS & STATISTICS
# ------------------------------------------------------------------------------

@login_required
def daily_session_report_view(request):
    session_id = request.GET.get('session')
    sex_filter = request.GET.get('sex')
    status_filter = request.GET.get('status')
    age_group_filter = request.GET.get('age_group')

    sessions = VaccinationSession.objects.all().order_by('-session_date')
    selected_session = VaccinationSession.objects.filter(id=session_id).first() if session_id else None

    report_data = generate_session_report(
        session_id=selected_session.id if selected_session else None,
        sex_filter=sex_filter,
        status_filter=status_filter,
        age_group_filter=age_group_filter
    )

    context = {
        'sessions': sessions,
        'selected_session': selected_session,
        'report_data': report_data,
        'sex_filter': sex_filter,
        'status_filter': status_filter,
        'age_group_filter': age_group_filter,
    }
    return render(request, 'reports/daily_session.html', context)

# ------------------------------------------------------------------------------
# ADMINISTRATION, AUDIT & SYSTEM HEALTH
# ------------------------------------------------------------------------------

@login_required
@require_role([ROLE_ADMIN])
def hospital_settings_view(request):
    setting = HospitalSetting.get_settings()
    if request.method == 'POST':
        form = HospitalSettingForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            form.save()
            log_audit_event(request.user, 'SETTINGS_UPDATED', 'HospitalSetting', setting.id, "Updated hospital configuration.")
            messages.success(request, "Hospital settings saved successfully.")
            return redirect('hospital_settings')
    else:
        form = HospitalSettingForm(instance=setting)

    return render(request, 'admin/settings.html', {'form': form})

@login_required
@require_role([ROLE_ADMIN])
def user_management_view(request):
    users = User.objects.all().select_related()
    return render(request, 'admin/users.html', {'users': users})

@login_required
@require_role([ROLE_ADMIN])
def audit_log_view(request):
    logs = AuditLog.objects.select_related('user').all()[:200]
    date_audits = SessionDateAudit.objects.select_related('session', 'changed_by').all()[:100]
    return render(request, 'admin/audit_log.html', {'logs': logs, 'date_audits': date_audits})

@login_required
@require_role([ROLE_ADMIN])
def system_health_view(request):
    latest_backup = BackupRecord.objects.first()
    db_status = "Connected (SQLite/PostgreSQL)"
    total_patients = Patient.objects.count()
    total_records = VaccinationRecord.objects.count()
    
    return render(request, 'admin/system_health.html', {
        'latest_backup': latest_backup,
        'db_status': db_status,
        'total_patients': total_patients,
        'total_records': total_records,
    })
