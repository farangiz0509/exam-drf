from rest_framework import serializers
from datetime import datetime
from django.utils import timezone
from clinic_api.apps.appointments.models import Appointment
from clinic_api.apps.users.serializers import UserSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for appointments"""
    
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    timeslot_date = serializers.CharField(source='timeslot.date', read_only=True)
    timeslot_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'doctor_name', 'patient', 'patient_name', 'timeslot', 
                  'timeslot_date', 'timeslot_time', 'status', 'created_at']
        read_only_fields = ['id', 'created_at', 'patient']
    
    def get_timeslot_time(self, obj):
        if obj.timeslot:
            return f"{obj.timeslot.start_time} - {obj.timeslot.end_time}"
        return None
    
    def validate(self, data):
        """Validate appointment"""
        request = self.context.get('request')
        request_user = getattr(request, 'user', None)

        # Prevent a doctor from booking an appointment with themselves
        if request_user and data.get('doctor') == request_user:
            raise serializers.ValidationError("Doctor cannot book appointment with themselves")

        # Check if appointment is in the past (timezone-aware)
        if data.get('timeslot'):
            appointment_datetime = datetime.combine(data['timeslot'].date, data['timeslot'].start_time)
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())
            if appointment_datetime < timezone.now():
                raise serializers.ValidationError("Cannot book appointment in the past")
        
        return data


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Details serializer for appointments"""
    
    doctor = UserSerializer(read_only=True)
    patient = UserSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'patient', 'timeslot', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'patient']


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointment status"""
    
    class Meta:
        model = Appointment
        fields = ['status']
    
    def validate_status(self, value):
        if value not in ['pending', 'confirmed', 'cancelled']:
            raise serializers.ValidationError("Invalid status")
        return value
