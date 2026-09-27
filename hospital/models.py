from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .nepali_date import ad_to_bs, format_bs_date, calculate_exact_age

class HospitalSetting(models.Model):
    hospital_name = models.CharField(max_length=255, default="Swarnabindu Government Hospital")
    nepali_hospital_name = models.CharField(max_length=255, default="स्वर्णविन्दु सरकारी अस्पताल")
    address = models.CharField(max_length=255, default="Ward No. 4, Hospital Road")
    district = models.CharField(max_length=100, default="Kavrepalanchok")
    municipality = models.CharField(max_length=100, default="Panauti Municipality")
    ward = models.CharField(max_length=20, default="04")
    province = models.CharField(max_length=100, default="Bagmati Province")
    phone = models.CharField(max_length=50, default="+977-01-5500000")
    email = models.EmailField(default="info@swarnabindu.gov.np")
    report_header = models.TextField(default="Government of Nepal\nMinistry of Health & Population\nSwarnabindu Vaccination Program")
    report_footer = models.TextField(default="This is an official hospital system report. Valid without manual signature if system verified.")
    logo = models.ImageField(upload_to='hospital/', null=True, blank=True)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return self.hospital_name

class Patient(models.Model):
    SEX_CHOICES = [
        ('M', 'Male (पुरुष)'),
        ('F', 'Female (महिला)'),
        ('O', 'Other (अन्य)'),
    ]

    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    child_name = models.CharField(max_length=150, verbose_name="Child Full Name")
    nepali_name = models.CharField(max_length=150, blank=True, verbose_name="Child Name (Nepali)")
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    date_of_birth = models.DateField(verbose_name="Date of Birth (AD)")
    guardian_name = models.CharField(max_length=150, verbose_name="Parent / Guardian Name")
    
    # CRITICAL RULE: Phone number MUST NOT be unique. Multiple children can share same phone.
    phone_number = models.CharField(max_length=20, db_index=True, verbose_name="Primary Phone Number")
    secondary_phone = models.CharField(max_length=20, blank=True, verbose_name="Secondary Phone")
    
    province = models.CharField(max_length=100, default="Bagmati Province")
    district = models.CharField(max_length=100, default="Kavrepalanchok")
    municipality = models.CharField(max_length=100, default="Panauti Municipality")
    ward = models.CharField(max_length=20, default="04")
    locality = models.CharField(max_length=150, verbose_name="Tole / Village / Address")
    
    identification_info = models.TextField(blank=True, help_text="Citizenship/Birth Certificate number of parent")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last_patient = Patient.objects.order_by('-id').first()
            if last_patient and last_patient.id:
                new_num = last_patient.id + 1
            else:
                new_num = 1
            self.patient_id = f"SW-{new_num:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.child_name}"

    @property
    def dob_bs(self):
        return format_bs_date(self.date_of_birth)

    @property
    def current_age_info(self):
        return calculate_exact_age(self.date_of_birth, timezone.now().date())

class VaccinationSession(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Open', 'Open'),
        ('Completed', 'Completed'),
        ('Postponed', 'Postponed'),
        ('Cancelled', 'Cancelled'),
    ]

    program_name = models.CharField(max_length=200, help_text="e.g. Swarnabindu Session 19 Ashoj 2083")
    session_date = models.DateField(help_text="Official session date")
    session_time = models.TimeField(default="09:00:00")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session_date']

    def __str__(self):
        return f"{self.program_name} ({format_bs_date(self.session_date)})"

    @property
    def session_date_bs(self):
        return format_bs_date(self.session_date)

class SessionDateAudit(models.Model):
    session = models.ForeignKey(VaccinationSession, on_delete=models.CASCADE, related_name='date_audits')
    old_date = models.DateField()
    new_date = models.DateField()
    reason = models.TextField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

class VaccinationRecord(models.Model):
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Missed', 'Missed'),
        ('Deferred', 'Deferred'),
        ('Cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vaccinations')
    vaccination_session = models.ForeignKey(VaccinationSession, on_delete=models.CASCADE, related_name='records')
    vaccination_date = models.DateField(default=timezone.now)
    
    # Exact age permanently stored at time of vaccination
    age_at_vaccination_years = models.IntegerField(default=0)
    age_at_vaccination_months = models.IntegerField(default=0)
    age_at_vaccination_days = models.IntegerField(default=0)
    age_at_vaccination_str = models.CharField(max_length=100)
    age_group = models.CharField(max_length=50, default='0–6 months')

    # Clinical Vitals
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, verbose_name="Height (cm)")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Weight (kg)")
    bp_systolic = models.IntegerField(null=True, blank=True, verbose_name="Systolic BP (mmHg)")
    bp_diastolic = models.IntegerField(null=True, blank=True, verbose_name="Diastolic BP (mmHg)")
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Temperature (°C)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')
    next_vaccination_session = models.ForeignKey(
        VaccinationSession, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='next_appointments'
    )
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate vaccination for same patient and session
        unique_together = ('patient', 'vaccination_session')
        ordering = ['-vaccination_date']

    def save(self, *args, **kwargs):
        # Always calculate and lock exact age on vaccination date
        if self.patient and self.vaccination_date:
            age_info = calculate_exact_age(self.patient.date_of_birth, self.vaccination_date)
            self.age_at_vaccination_years = age_info['years']
            self.age_at_vaccination_months = age_info['months']
            self.age_at_vaccination_days = age_info['days']
            self.age_at_vaccination_str = age_info['formatted']
            self.age_group = age_info['age_group']
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.patient_id} - {self.vaccination_session.program_name}"

    @property
    def vaccination_date_bs(self):
        return format_bs_date(self.vaccination_date)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action} by {self.user}"

class BackupRecord(models.Model):
    filename = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    file_size_bytes = models.BigIntegerField(default=0)
    status = models.CharField(max_length=50, default='Verified')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
