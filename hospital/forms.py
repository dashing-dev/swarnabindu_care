from django import forms
from django.core.exceptions import ValidationError
from .models import Patient, VaccinationSession, VaccinationRecord, HospitalSetting
from .nepali_date import bs_to_ad, ad_to_bs, format_bs_date, parse_bs_string
import datetime

class PatientForm(forms.ModelForm):
    dob_bs_input = forms.CharField(
        label="Date of Birth (BS)", 
        help_text="Format: YYYY-MM-DD or e.g. 19 Ashoj 2081",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 2081-06-19', 'class': 'form-control'})
    )

    class Meta:
        model = Patient
        fields = [
            'child_name', 'nepali_name', 'sex', 'guardian_name', 
            'phone_number', 'secondary_phone', 'province', 'district', 
            'municipality', 'ward', 'locality', 'identification_info', 'notes'
        ]
        widgets = {
            'child_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nepali_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional Nepali Script'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'ward': forms.TextInput(attrs={'class': 'form-control'}),
            'locality': forms.TextInput(attrs={'class': 'form-control'}),
            'identification_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.date_of_birth:
            y, m, d = ad_to_bs(self.instance.date_of_birth)
            self.fields['dob_bs_input'].initial = f"{y:04d}-{m:02d}-{d:02d}"

    def clean_dob_bs_input(self):
        bs_val = self.cleaned_data.get('dob_bs_input')
        parsed_ad = parse_bs_string(bs_val)
        if not parsed_ad:
            raise ValidationError("Invalid Nepali Date format. Please enter as YYYY-MM-DD (e.g., 2081-06-19).")
        if parsed_ad > datetime.date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return parsed_ad

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.date_of_birth = self.cleaned_data['dob_bs_input']
        if commit:
            instance.save()
        return instance

class VaccinationSessionForm(forms.ModelForm):
    session_date_bs = forms.CharField(
        label="Session Date (BS)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 2083-06-19', 'class': 'form-control'})
    )

    class Meta:
        model = VaccinationSession
        fields = ['program_name', 'session_time', 'status', 'notes']
        widgets = {
            'program_name': forms.TextInput(attrs={'class': 'form-control'}),
            'session_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.session_date:
            y, m, d = ad_to_bs(self.instance.session_date)
            self.fields['session_date_bs'].initial = f"{y:04d}-{m:02d}-{d:02d}"

    def clean_session_date_bs(self):
        bs_val = self.cleaned_data.get('session_date_bs')
        parsed_ad = parse_bs_string(bs_val)
        if not parsed_ad:
            raise ValidationError("Invalid Nepali date format. Example: 2083-06-19.")
        return parsed_ad

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.session_date = self.cleaned_data['session_date_bs']
        if commit:
            instance.save()
        return instance

class SessionDateChangeForm(forms.Form):
    new_date_bs = forms.CharField(
        label="New Session Date (BS)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 2083-06-20', 'class': 'form-control'})
    )
    reason = forms.CharField(
        label="Official Reason for Date Change / Postponement",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. Hospital public holiday reschedule.'})
    )

    def clean_new_date_bs(self):
        bs_val = self.cleaned_data.get('new_date_bs')
        parsed_ad = parse_bs_string(bs_val)
        if not parsed_ad:
            raise ValidationError("Invalid Nepali date format.")
        return parsed_ad

class VaccinationRecordForm(forms.ModelForm):
    class Meta:
        model = VaccinationRecord
        fields = [
            'vaccination_session', 'height_cm', 'weight_kg', 
            'bp_systolic', 'bp_diastolic', 'temperature_c', 
            'status', 'next_vaccination_session', 'notes'
        ]
        widgets = {
            'vaccination_session': forms.Select(attrs={'class': 'form-select'}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bp_systolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 90'}),
            'bp_diastolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 60'}),
            'temperature_c': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'value': '36.6'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'next_vaccination_session': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        # Filter next session choices to active/future scheduled sessions
        self.fields['next_vaccination_session'].queryset = VaccinationSession.objects.exclude(status='Cancelled').order_by('session_date')
        self.fields['next_vaccination_session'].required = False

    def clean(self):
        cleaned_data = super().clean()
        session = cleaned_data.get('vaccination_session')
        
        # Check duplicate vaccination for same session
        if self.patient and session:
            existing = VaccinationRecord.objects.filter(patient=self.patient, vaccination_session=session)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(
                    f"DUPLICATE VACCINATION PREVENTED: Patient {self.patient.patient_id} has already been registered/vaccinated for session '{session.program_name}'."
                )

        # Vitals clinical range validations
        height = cleaned_data.get('height_cm')
        weight = cleaned_data.get('weight_kg')
        temp = cleaned_data.get('temperature_c')

        if height and (height < 20.0 or height > 200.0):
            self.add_error('height_cm', "Height value outside reasonable clinical range (20 - 200 cm).")
        if weight and (weight < 0.5 or weight > 100.0):
            self.add_error('weight_kg', "Weight value outside reasonable clinical range (0.5 - 100 kg).")
        if temp and (temp < 30.0 or temp > 45.0):
            self.add_error('temperature_c', "Body temperature outside clinical limits (30 - 45 °C).")

        return cleaned_data

class HospitalSettingForm(forms.ModelForm):
    class Meta:
        model = HospitalSetting
        fields = [
            'hospital_name', 'nepali_hospital_name', 'address', 'district',
            'municipality', 'ward', 'province', 'phone', 'email',
            'report_header', 'report_footer'
        ]
        widgets = {
            'hospital_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nepali_hospital_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'ward': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'report_header': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'report_footer': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
