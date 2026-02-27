from django.db import models
from django.core.exceptions import ValidationError
from clinic_api.apps.users.models import User
from clinic_api.apps.doctors.models import TimeSlot


class Appointment(models.Model):
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments', limit_choices_to={'role': 'doctor'})
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments', limit_choices_to={'role': 'patient'})
    timeslot = models.OneToOneField(TimeSlot, on_delete=models.SET_NULL, null=True, related_name='appointment')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointments'
        ordering = ['-created_at']
        unique_together = ('patient', 'timeslot')
    
    def __str__(self):
        return f"Appointment: {self.patient.username} with Dr. {self.doctor.username} - {self.status}"
    
    def clean(self):
        if self.doctor == self.patient:
            raise ValidationError("Doctor cannot book appointment with themselves")
        if self.timeslot and not self.pk and not self.timeslot.is_available:
            raise ValidationError("This time slot is not available")
        if self.timeslot and self.timeslot.doctor != self.doctor:
            raise ValidationError("Time slot does not belong to this doctor")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update timeslot availability
        if self.status == 'cancelled' and self.timeslot:
            self.timeslot.is_available = True
            self.timeslot.save()
        elif self.timeslot:
            self.timeslot.is_available = False
            self.timeslot.save()
