from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=100)
    bio = models.TextField()
    checkup_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_lab_tester = models.BooleanField(default=False)

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"Dr. {name}"


class Patient(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True,blank=True)
    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50)
    dob        = models.DateField(verbose_name="Date of Birth")
    email      = models.EmailField()
    phone      = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

class Appointment(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    doctor = models.ForeignKey('DoctorProfile', on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField()
    queue_number = models.IntegerField(null=True, blank=True)
    checkup_done = models.BooleanField(default=False)
    is_lab_test = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Custom save method that recalculates queue_number for appointments
        on the same local calendar date, for either lab test or a specific doctor.
        """
        # Debug: Indicate that save() was called
        print(f"[DEBUG] Appointment.save() called for ID={self.pk} "
              f"date={self.appointment_date}, is_lab_test={self.is_lab_test}")

        # A flag to prevent recursion on subsequent .save() calls
        recalc = kwargs.pop('_recalc', True)

        # First, save the Appointment normally
        super().save(*args, **kwargs)

        if recalc:
            # Convert the appointment date to local time so we can filter by local date
            local_dt = timezone.localtime(self.appointment_date)
            local_date = local_dt.date()

            print(f"[DEBUG] Local date for appointment ID={self.pk} is {local_date}")

            if self.is_lab_test:
                # Lab testers see all lab test appointments on the same local date
                print("[DEBUG] This is a lab test appointment. "
                      "Filtering all lab test appointments for the same local date.")
                qs = Appointment.objects.filter(
                    is_lab_test=True,
                    checkup_done=False,
                    appointment_date__range=(
                        datetime.datetime.combine(local_date, datetime.time.min, local_dt.tzinfo),
                        datetime.datetime.combine(local_date, datetime.time.max, local_dt.tzinfo),
                    )
                ).order_by('appointment_date')
            else:
                # For non-lab test appointments, filter by the same doctor on the same local date
                print(f"[DEBUG] This is a doctor appointment for doctor={self.doctor}. "
                      "Filtering appointments for the same local date.")
                qs = Appointment.objects.filter(
                    doctor=self.doctor,
                    is_lab_test=False,
                    checkup_done=False,
                    appointment_date__range=(
                        datetime.datetime.combine(local_date, datetime.time.min, local_dt.tzinfo),
                        datetime.datetime.combine(local_date, datetime.time.max, local_dt.tzinfo),
                    )
                ).order_by('appointment_date')

            print(f"[DEBUG] Found {qs.count()} appointments to re-sequence on {local_date}.")

            # Enumerate over the appointments, assigning queue_number in chronological order
            for idx, app in enumerate(qs, start=1):
                print(f"[DEBUG] Checking ID={app.pk}, old queue_number={app.queue_number}, new idx={idx}")
                if app.queue_number != idx:
                    app.queue_number = idx
                    # Save again without triggering recursion
                    app.save(_recalc=False, update_fields=['queue_number'])
                    print(f"[DEBUG] Updated queue_number to {idx} for ID={app.pk}")

    def __str__(self):
        return f"Appointment for {self.patient} on {self.appointment_date}"

class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    bio = models.TextField()

    def __str__(self):
        return self.name
    

class LabTest(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class HealthArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateField()
    trending = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    # Optionally include stock, expiry, etc.

    def __str__(self):
        return self.name

class MedicineOrder(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='Pending')  # e.g. Pending, Confirmed, Delivered, Cancelled
    order_number = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Save the order first so that order_date is set.
        super().save(*args, **kwargs)
        # Recalculate order numbers for all orders for this patient,
        # ordered by order_date (oldest first)
        orders = MedicineOrder.objects.filter(patient=self.patient).order_by('order_date')
        for idx, order in enumerate(orders, start=1):
            if order.order_number != idx:
                # Use update() to avoid recursive calls to save()
                MedicineOrder.objects.filter(pk=order.pk).update(order_number=idx)

    def __str__(self):
        # Show the order number if available, otherwise fallback to primary key.
        return f"Order {self.order_number or self.id} by {self.patient}"

    
