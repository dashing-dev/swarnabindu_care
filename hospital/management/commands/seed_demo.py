from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hospital.models import Patient, VaccinationSession, VaccinationRecord, HospitalSetting
from hospital.nepali_date import bs_to_ad
from hospital.permissions import ROLE_ADMIN, ROLE_OPERATOR, ROLE_READONLY
import datetime

class Command(BaseCommand):
    help = 'Seeds fictitious demo hospital data.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Swarnabindu Hospital demo data...")

        # Initialize Groups
        admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        operator_group, _ = Group.objects.get_or_create(name=ROLE_OPERATOR)
        readonly_group, _ = Group.objects.get_or_create(name=ROLE_READONLY)

        # Users
        admin_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@hospital.gov.np', 'is_staff': True, 'is_superuser': True})
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            admin_user.groups.add(admin_group)

        operator_user, created = User.objects.get_or_create(username='operator', defaults={'email': 'operator@hospital.gov.np'})
        if created:
            operator_user.set_password('operator123')
            operator_user.save()
            operator_user.groups.add(operator_group)

        # Hospital Settings
        HospitalSetting.get_settings()

        # Sessions (BS dates)
        s1, _ = VaccinationSession.objects.get_or_create(
            program_name="Swarnabindu Routine Session 19 Ashoj 2083",
            defaults={
                'session_date': bs_to_ad(2083, 6, 19),
                'status': 'Completed',
                'created_by': admin_user
            }
        )

        s2, _ = VaccinationSession.objects.get_or_create(
            program_name="Swarnabindu Routine Session 18 Kartik 2083",
            defaults={
                'session_date': bs_to_ad(2083, 7, 18),
                'status': 'Scheduled',
                'created_by': admin_user
            }
        )

        s3, _ = VaccinationSession.objects.get_or_create(
            program_name="Swarnabindu Routine Session 20 Mangsir 2083",
            defaults={
                'session_date': bs_to_ad(2083, 8, 20),
                'status': 'Scheduled',
                'created_by': admin_user
            }
        )

        # Demonstrating Phone Non-Uniqueness: Parent Ramesh Shrestha has TWO children sharing 9841000000
        p1, _ = Patient.objects.get_or_create(
            patient_id="SW-000001",
            defaults={
                'child_name': "Aarav Shrestha",
                'nepali_name': "आरभ श्रेष्ठ",
                'sex': 'M',
                'date_of_birth': bs_to_ad(2081, 2, 10),
                'guardian_name': "Ramesh Shrestha",
                'phone_number': "9841000000",
                'locality': "Taukhal, Panauti"
            }
        )

        p2, _ = Patient.objects.get_or_create(
            patient_id="SW-000002",
            defaults={
                'child_name': "Aarya Shrestha",
                'nepali_name': "आर्या श्रेष्ठ",
                'sex': 'F',
                'date_of_birth': bs_to_ad(2082, 5, 15),
                'guardian_name': "Ramesh Shrestha",
                'phone_number': "9841000000", # Same phone number!
                'locality': "Taukhal, Panauti"
            }
        )

        # Record Vaccination
        VaccinationRecord.objects.get_or_create(
            patient=p1,
            vaccination_session=s1,
            defaults={
                'vaccination_date': s1.session_date,
                'height_cm': 72.5,
                'weight_kg': 9.1,
                'bp_systolic': 90,
                'bp_diastolic': 60,
                'temperature_c': 36.6,
                'status': 'Completed',
                'next_vaccination_session': s2,
                'operator': operator_user,
                'notes': 'Normal administration without adverse reaction.'
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully! Login: admin/admin123 or operator/operator123"))
