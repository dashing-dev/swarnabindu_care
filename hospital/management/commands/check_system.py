from django.core.management.base import BaseCommand
from hospital.models import Patient, VaccinationSession, VaccinationRecord

class Command(BaseCommand):
    help = 'Checks system health and integrity.'

    def handle(self, *args, **options):
        self.stdout.write("Running Swarnabindu Hospital System Check...")
        patients = Patient.objects.count()
        sessions = VaccinationSession.objects.count()
        records = VaccinationRecord.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f"System Operational! Total Patients: {patients}, Sessions: {sessions}, Records: {records}"))
