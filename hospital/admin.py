from django.contrib import admin
from .models import Patient, VaccinationSession, VaccinationRecord, SessionDateAudit, AuditLog, HospitalSetting, BackupRecord

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'child_name', 'nepali_name', 'sex', 'date_of_birth', 'guardian_name', 'phone_number')
    search_fields = ('patient_id', 'child_name', 'guardian_name', 'phone_number')

@admin.register(VaccinationSession)
class VaccinationSessionAdmin(admin.ModelAdmin):
    list_display = ('program_name', 'session_date', 'status', 'created_by')
    list_filter = ('status',)

@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'vaccination_session', 'vaccination_date', 'age_at_vaccination_str', 'status')
    list_filter = ('status', 'age_group')

admin.site.register(HospitalSetting)
admin.site.register(SessionDateAudit)
admin.site.register(AuditLog)
admin.site.register(BackupRecord)
