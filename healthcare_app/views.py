from django.shortcuts import get_object_or_404,render, redirect
from .forms import PatientRegistrationForm
from django.contrib.auth.decorators import login_required
from .forms import AppointmentForm
from .models import LabTest, HealthArticle, MedicineOrder, Appointment, DoctorProfile, Patient,Medicine
from .forms import PatientForm
from .forms import DoctorRegistrationForm
from django.http import HttpResponse
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
import requests
import random


def home(request):
    return render(request, 'healthcare_app/index.html')

def index(request):
    return render(request, 'healthcare_app/index.html')

def lab_tests(request):
    tests = LabTest.objects.all().order_by('name')
    return render(request, 'healthcare_app/lab_tests.html', {'tests': tests})

@login_required
def book_lab_test(request, test_id):
    test = get_object_or_404(LabTest, id=test_id)
    if request.method == "POST":
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            messages.error(request, "Please create your patient profile to book lab tests.")
            return redirect('patient_create')
        schedule_date_str = request.POST.get('schedule_date')
        try:
            schedule_date = datetime.strptime(schedule_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            return render(request, 'healthcare_app/book_lab_test.html', {'test': test, 'error': 'Invalid date format.'})
        
        # If the appointment date is naive, make it aware using the current timezone.
        if timezone.is_naive(schedule_date):
            schedule_date = timezone.make_aware(schedule_date, timezone.get_current_timezone())
        
        # Validate that the schedule date is in the future.
        if schedule_date <= timezone.now():
            return render(request, 'healthcare_app/book_lab_test.html', {
                'test': test,
                'error': 'Please enter a future date and time.'
            })
         
        # Create a lab test appointment with no assigned doctor and flag it as lab test.
        appointment = Appointment.objects.create(
            patient=patient,
            appointment_date=schedule_date,
            doctor=None,
            reason=f"Lab Test Booking: {test.name}",
            is_lab_test=True
        )
        return render(request, 'healthcare_app/lab_test_booking_confirm.html', {'appointment': appointment})
    return render(request, 'healthcare_app/book_lab_test.html', {'test': test})

@login_required
def buy_medicine(request):
    # Retrieve all available medicines, you might order them by name.
    medicines = Medicine.objects.all().order_by('name')
    return render(request, 'healthcare_app/buy_medicine.html', {'medicines': medicines})

def health_articles(request):
    articles = HealthArticle.objects.filter(trending=True).order_by('-published_date')
    return render(request, 'healthcare_app/health_articles.html', {'articles': articles})

def article_detail(request, article_id):
    article = get_object_or_404(HealthArticle, id=article_id)
    return render(request, 'healthcare_app/article_detail.html', {'article': article})

@login_required
def order_details(request):
    # Fetch all orders for the logged-in patient.
    orders = MedicineOrder.objects.filter(patient__user=request.user).order_by('-order_date')
    return render(request, 'healthcare_app/order_details.html', {'orders': orders})

@login_required
def patient_profile(request):
    try:
        patient = Patient.objects.get(user=request.user)
        return render(request, 'healthcare_app/patient_profile.html', {'patient': patient})
    except Patient.DoesNotExist:
        messages.error(request, "Please create your patient profile first.")
        return redirect('patient_create')

@login_required
def doctor_profile(request):
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
        return render(request, 'healthcare_app/doctor_profile.html', {'doctor': doctor})
    except DoctorProfile.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_dashboard')

def doctor_list(request):
    genre = request.GET.get('genre', None)
    if genre and genre.lower() != 'all':
        doctors = DoctorProfile.objects.filter(specialty__icontains=genre, is_lab_tester=False)
    else:
        doctors = DoctorProfile.objects.filter(is_lab_tester=False)

    doctor_list_with_rating = []
    for doctor in doctors:
        random.seed(doctor.id)  # deterministic rating per doctor
        rating = round(random.uniform(3.0, 5.0), 1)
        star_rating = int(round(rating))  # convert to integer for star display
        doctor_list_with_rating.append({
            'doctor': doctor,
            'rating': rating,
            'star_rating': star_rating
        })
    
    return render(request, 'healthcare_app/doctor_list.html', {
        'doctor_list': doctor_list_with_rating,
        'genre': genre
    })



def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the new user to the database
            return redirect('login')  # Redirect to login page after registration
    else:
        form = PatientRegistrationForm()
    return render(request, 'healthcare_app/register.html', {'form': form})

@login_required    
def book_appointment(request):
    
    initial = {}
    doctor_id = request.GET.get('doctor')
    if doctor_id:
        initial['doctor'] = doctor_id  # set the initial doctor value

    if request.method == "POST":
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('appointment_list')
    else:
        form = AppointmentForm(initial=initial,user=request.user)
    return render(request, 'healthcare_app/appointment.html', {'form': form})


@login_required  
def appointment_list(request):
        appointments = Appointment.objects.filter(patient__user=request.user)
        return render(request, 'healthcare_app/appointment_list.html', {'appointments': appointments})

@login_required  
def appointment_list(request):
    if getattr(request.user, 'is_authenticated', False):
        # For logged-in users, show appointments only for patients associated with them.
        appointments = Appointment.objects.filter(patient__user=request.user)
    else:
        # For anonymous users, show all appointments (or change to Appointment.objects.none() if desired)
        appointments = Appointment.objects.all()
    
    return render(request, 'healthcare_app/appointment_list.html', {'appointments': appointments})


def about(request):
    return render(request, 'healthcare_app/about.html')

@login_required
def patient_list(request):
    # Show only the patients belonging to the logged-in user
    patients = Patient.objects.filter(user=request.user)
    return render(request, 'healthcare_app/patient_list.html', {'patients': patients})

@login_required
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user  # Associate with the logged-in user
            patient.save()
            return redirect('patient_list')
        else:
            # Optional: print or log form.errors for debugging
            print(form.errors)
    else:
        form = PatientForm()

    return render(request, 'healthcare_app/patient_create.html', {'form': form})


def doctor_register(request):
    if request.method == "POST":
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('doctor_login')
    else:
        form = DoctorRegistrationForm()
    return render(request, 'healthcare_app/doctor_register.html', {'form': form})


@login_required
def doctor_dashboard(request):
    try:
        doctor_profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        return redirect('doctor_register')

    hide_completed = request.GET.get('hide_completed') == '1'

    # Determine which appointments to show
    if doctor_profile.is_lab_tester:
        # Lab testers see all lab test appointments
        appointments = Appointment.objects.filter(is_lab_test=True).order_by('appointment_date')
        print("[DEBUG] doctor_dashboard: Lab tester account, showing lab test appointments.")
    else:
        # Regular doctors see only their appointments
        appointments = Appointment.objects.filter(
            doctor=doctor_profile,
            is_lab_test=False
        ).order_by('appointment_date')
        print(f"[DEBUG] doctor_dashboard: Regular doctor={doctor_profile}, showing assigned appointments.")

    # Optionally hide completed checkups
    if hide_completed:
        appointments = appointments.filter(checkup_done=False)
        print("[DEBUG] doctor_dashboard: Hiding completed checkups.")

    # Refresh each appointment from the DB to ensure queue_number is up to date
    for app in appointments:
        print(f"[DEBUG] Before refresh: ID={app.pk}, queue_number={app.queue_number}")
        app.refresh_from_db(fields=['queue_number'])
        print(f"[DEBUG] After refresh: ID={app.pk}, queue_number={app.queue_number}")

    context = {
        'appointments': appointments,
        'hide_completed': hide_completed,
    }
    return render(request, 'healthcare_app/doctor_dashboard.html', context)

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    # Ensure the appointment belongs to the logged-in user (assuming patient appointments)
    if appointment.patient.user == request.user:
        appointment.delete()
    # Optionally, add messages.success(request, "Appointment cancelled successfully.")
    return redirect('appointment_list')


@login_required
def mark_checkup_done(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if appointment.is_lab_test:
        # For lab test appointments, check if the user is a lab tester
        try:
            if request.user.doctorprofile.is_lab_tester:
                appointment.checkup_done = True
                appointment.save()
        except AttributeError:
            # If the logged-in user doesn't have a doctorprofile
            pass
    else:
        # For regular appointments, check if the appointment's doctor matches the logged-in user
        if appointment.doctor and appointment.doctor.user == request.user:
            appointment.checkup_done = True
            appointment.save()
    
    return redirect('doctor_dashboard')


@login_required
def clear_completed_checkups(request):
    try:
        doctor_profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        return redirect('doctor_register')
    
    if request.method == "POST":
        if doctor_profile.is_lab_tester:
            # For lab testers, clear all completed lab test appointments.
            Appointment.objects.filter(is_lab_test=True, checkup_done=True).delete()
        else:
            # For regular doctors, clear only completed appointments assigned to them.
            Appointment.objects.filter(doctor=doctor_profile, checkup_done=True, is_lab_test=False).delete()
    return redirect('doctor_dashboard')



@login_required
def order_medicine(request, medicine_id):
    # Get the selected medicine; if not found, return 404.
    medicine = get_object_or_404(Medicine, id=medicine_id)
    
    # Ensure the logged-in user has an associated Patient profile.
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, "Please create your patient profile to order medicine.")
        return redirect('patient_create')

    # Create a new medicine order. For simplicity, one order equals one medicine.
    order = MedicineOrder.objects.create(
        patient=patient,
        medicine=medicine,
        total_price=medicine.price,
        status='Pending'
    )
    # Optionally, you might update medicine stock here.
    # Redirect the user to the order details page.
    return redirect('order_details')


@login_required
def cancel_medicine_order(request, order_id):
    order = get_object_or_404(MedicineOrder, id=order_id, patient__user=request.user)
    # Allow cancellation only if the order status is 'Pending'
    if order.status.lower() == "pending":
        order.status = "Cancelled"
        order.save()
    return redirect('order_details')

@login_required
def clear_order_entries(request):
    if request.method == "POST":
        # Delete orders that are either Completed or Cancelled for the logged-in user
        MedicineOrder.objects.filter(
            patient__user=request.user,
            status__in=["Completed", "Cancelled"]
        ).delete()
        # Recalculate order numbers for the remaining orders for this patient
        try:
            patient = Patient.objects.get(user=request.user)
            orders = MedicineOrder.objects.filter(patient=patient).order_by('order_date')
            for idx, order in enumerate(orders, start=1):
                if order.order_number != idx:
                    MedicineOrder.objects.filter(pk=order.pk).update(order_number=idx)
        except Patient.DoesNotExist:
            pass  # If no patient profile exists, nothing to recalc.
    return redirect('order_details')



def fetch_trending_articles_gnews(request):
    api_key = settings.GNEWS_API_KEY
    # Fetch top health headlines for India (adjust country and category as needed)
    url = f"https://gnews.io/api/v4/top-headlines?category=health&country=in&apikey={api_key}"
    response = requests.get(url)
    articles = []
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])
    else:
        print("GNews API error:", response.text)
    return render(request, 'healthcare_app/health_articles_external.html', {'articles': articles})


@login_required
def patient_edit(request, patient_id):
    # Only allow editing if the patient belongs to the logged-in user.
    patient = get_object_or_404(Patient, id=patient_id, user=request.user)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('patient_list')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'healthcare_app/patient_edit.html', {'form': form, 'patient': patient})

@login_required
def patient_delete(request, patient_id):
    # Only allow deletion if the patient belongs to the logged-in user.
    patient = get_object_or_404(Patient, id=patient_id, user=request.user)
    if request.method == 'POST':
        patient.delete()
        messages.success(request, "Your profile has been deleted.")
        return redirect('patient_list')
    return render(request, 'healthcare_app/patient_confirm_delete.html', {'patient': patient})


@login_required
def clear_completed_appointments(request):
    if request.method == "POST":
        # Delete all appointments where checkup_done=True for the logged-in user
        Appointment.objects.filter(
            patient__user=request.user,
            checkup_done=True
        ).delete()
    return redirect('appointment_list')