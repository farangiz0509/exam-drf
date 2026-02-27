from django.db import models
from clinic_api.apps.users.models import User


class DoctorProfile(models.Model):
    """Doctor profile model"""
    
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    experience_years = models.IntegerField(default=0)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctor_profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization}"


class TimeSlot(models.Model):
    """Time slot model for doctor schedules"""
    
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_slots', limit_choices_to={'role': 'doctor'})
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'time_slots'
        ordering = ['date', 'start_time']
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
    
    def __str__(self):
        return f"{self.doctor.username} - {self.date} {self.start_time}-{self.end_time}"
    
    def is_overlap(self, other_start_time, other_end_time):
        """Check if this time slot overlaps with another time slot"""
        return not (self.end_time <= other_start_time or self.start_time >= other_end_time)
