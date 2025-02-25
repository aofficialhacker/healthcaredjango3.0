# healthcare_app/forms.py
from django import forms
from django.core.validators import RegexValidator
from .models import Appointment, Patient
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import DoctorProfile
from django.core.exceptions import ValidationError
from django.utils import timezone


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'appointment_date', 'doctor', 'reason']
        labels = {
            'patient': 'Select Patient',
            'appointment_date': 'Date & Time',
            'doctor': 'Doctor Name',
            'reason': 'Reason for Appointment',
        }
        help_texts = {
            'appointment_date': 'Choose a suitable date and time.',
            'reason': 'Describe the reason or symptoms for this appointment.',
        }
        widgets = {
            'patient': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'appointment_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'placeholder': 'YYYY-MM-DD HH:MM',
                }
            ),
            'doctor': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'reason': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Briefly describe your reason or symptoms',
                }
            ),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Expect the view to pass the logged-in user
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = DoctorProfile.objects.filter(is_lab_tester=False)
        if user:
            self.fields['patient'].queryset = Patient.objects.filter(user=user)
        else:
            self.fields['patient'].queryset = Patient.objects.none()

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date:
            # If the appointment_date is naive, assume it's in the local timezone.
            if timezone.is_naive(appointment_date):
                appointment_date = timezone.make_aware(appointment_date, timezone.get_current_timezone())
            now = timezone.now()
            # Debug: Uncomment the following two lines to log the values during testing.
            # print("Appointment Date:", appointment_date)
            # print("Now:", now)
            if appointment_date <= now:
                raise forms.ValidationError("Please enter a future date and time.")
        return appointment_date



class PatientForm(forms.ModelForm):
    # Example phone regex validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    # Override the phone field to include validation
    phone = forms.CharField(
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. +1234567890'
        })
    )

    # Override the dob (Date of Birth) field to use an HTML5 date picker
    dob = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',         # HTML5 date input
                'class': 'form-control'
            }
        ),
        label="Date of Birth"
    )

    # Override the email field to use HTML5 email input
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com'
        })
    )

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'dob', 'email', 'phone','address']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your address',
                'rows': 3
            }),
        }

SPECIALTY_CHOICES = [
    ('neurologist', 'Neurologist'),
    ('general_physician', 'General Physician'),
    ('gynecologist', 'Gynecologist'),
    ('cardiologist', 'Cardiologist'),
    ('dentist', 'Dentist'),
    ('dietician', 'Dietician'),
    ('orthopedist', 'Orthopedist'),
    ('dermatologist', 'Dermatologist'),
    ('psychiatrist', 'Psychiatrist'),
    ('pediatrician', 'Pediatrician'),
    ('ent', 'ENT'),
]


class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'username', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

class DoctorRegistrationForm(UserCreationForm):
    name = forms.CharField(
        max_length=100, 
        required=True, 
        label="Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}))
    
    email = forms.EmailField(required=True)
    specialty = forms.ChoiceField(choices=SPECIALTY_CHOICES)
    bio = forms.CharField(widget=forms.Textarea, required=True)
    checkup_fee = forms.DecimalField(
        max_digits=8, decimal_places=2, required=True,
        help_text="Enter your consultation fee in INR."
    )
    is_lab_tester = forms.BooleanField(
        required=False, 
        label="Register as Lab Tester (For Lab Test Appointments Only)"
    )

    class Meta:
        model = User
        fields = ['username','name', 'email', 'specialty', 'bio', 'checkup_fee', 'is_lab_tester', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['name']
        if commit:
            user.save()
            DoctorProfile.objects.create(
                user=user, 
                specialty=self.cleaned_data['specialty'], 
                bio=self.cleaned_data['bio'], 
                checkup_fee=self.cleaned_data['checkup_fee'],
                is_lab_tester=self.cleaned_data.get('is_lab_tester', False)
            )
        return user