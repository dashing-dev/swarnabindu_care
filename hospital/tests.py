from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import Patient, VaccinationSession, VaccinationRecord, SessionDateAudit, AuditLog
from .nepali_date import calculate_exact_age, bs_to_ad, ad_to_bs, format_bs_date
from .permissions import ROLE_ADMIN, ROLE_OPERATOR, ROLE_READONLY
import datetime

class AgeCalculationTests(TestCase):
    def test_exact_age_same_day(self):
        dob = datetime.date(2024, 1, 1)
        ref = datetime.date(2024, 1, 1)
        age = calculate_exact_age(dob, ref)
        self.assertEqual(age['years'], 0)
        self.assertEqual(age['months'], 0)
        self.assertEqual(age['days'], 0)
        self.assertEqual(age['age_group'], '0–6 months')

    def test_exact_age_month_boundaries(self):
        dob = datetime.date(2023, 5, 15)
        ref = datetime.date(2024, 6, 16)
        age = calculate_exact_age(dob, ref)
        self.assertEqual(age['years'], 1)
        self.assertEqual(age['months'], 1)
        self.assertEqual(age['days'], 1)
        self.assertEqual(age['age_group'], '1–2 years')

    def test_under_one_year_age_groups(self):
        dob = datetime.date(2024, 1, 1)
        ref = datetime.date(2024, 4, 1) # 3 months
        age = calculate_exact_age(dob, ref)
        self.assertEqual(age['age_group'], '0–6 months')

        ref8 = datetime.date(2024, 9, 1) # 8 months
        age8 = calculate_exact_age(dob, ref8)
        self.assertEqual(age8['age_group'], '6–12 months')

class PatientAndPhoneTests(TestCase):
    def test_multiple_children_same_phone(self):
        p1 = Patient.objects.create(
            child_name="Child A",
            sex='M',
            date_of_birth=datetime.date(2023, 1, 1),
            guardian_name="Parent X",
            phone_number="9841111111",
            locality="Panauti"
        )
        p2 = Patient.objects.create(
            child_name="Child B",
            sex='F',
            date_of_birth=datetime.date(2024, 2, 2),
            guardian_name="Parent X",
            phone_number="9841111111", # Non-unique phone number!
            locality="Panauti"
        )
        self.assertEqual(Patient.objects.filter(phone_number="9841111111").count(), 2)

class SessionAndVaccinationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
        self.session1 = VaccinationSession.objects.create(
            program_name="Session 19 Ashoj 2083",
            session_date=datetime.date(2024, 10, 5),
            created_by=self.admin
        )
        self.session2 = VaccinationSession.objects.create(
            program_name="Session 18 Kartik 2083",
            session_date=datetime.date(2024, 11, 4),
            created_by=self.admin
        )
        self.patient = Patient.objects.create(
            child_name="Test Child",
            sex='M',
            date_of_birth=datetime.date(2024, 1, 1),
            guardian_name="Test Guardian",
            phone_number="9840000000",
            locality="Banepa"
        )

    def test_duplicate_vaccination_prevention(self):
        VaccinationRecord.objects.create(
            patient=self.patient,
            vaccination_session=self.session1,
            height_cm=60.0,
            weight_kg=6.5,
            temperature_c=36.5,
            operator=self.admin
        )
        with self.assertRaises(Exception):
            # Enforce database uniqueness constraint
            VaccinationRecord.objects.create(
                patient=self.patient,
                vaccination_session=self.session1,
                height_cm=61.0,
                weight_kg=6.6,
                temperature_c=36.6,
                operator=self.admin
            )

    def test_session_date_change_audit(self):
        client = Client()
        client.force_login(self.admin)
        url = reverse('session_change_date', args=[self.session1.id])
        res = client.post(url, {
            'new_date_bs': '2083-06-20',
            'reason': 'Official hospital holiday'
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(SessionDateAudit.objects.count(), 1)
        audit = SessionDateAudit.objects.first()
        self.assertEqual(audit.reason, 'Official hospital holiday')
