from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from clinic_api.apps.users.models import User
from clinic_api.apps.doctors.models import DoctorProfile, TimeSlot
from clinic_api.apps.patients.models import PatientProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Password Confirmation')
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role']
    
    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({"password": "Passwords must match."})
        
        # Additional validation for role
        if data.get('role') not in ['doctor', 'patient', 'admin']:
            raise serializers.ValidationError({"role": "Invalid role"})
        
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        
        # Create profile based on role
        if user.role == 'doctor':
            DoctorProfile.objects.create(
                user=user,
                specialization='General',
                experience_years=0,
                gender='male'
            )
        elif user.role == 'patient':
            PatientProfile.objects.create(
                user=user,
                phone='',
                date_of_birth='2000-01-01',
                gender='male'
            )
        
        return user


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Serializer for doctor profile"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'specialization', 'experience_years', 'gender', 'created_at']
        read_only_fields = ['id', 'created_at']


class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating doctor profile"""
    
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'experience_years', 'gender']


class PatientProfileSerializer(serializers.ModelSerializer):
    """Serializer for patient profile"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'phone', 'date_of_birth', 'gender', 'created_at']
        read_only_fields = ['id', 'created_at']


class PatientProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating patient profile"""
    
    class Meta:
        model = PatientProfile
        fields = ['phone', 'date_of_birth', 'gender']


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for time slots"""
    
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'doctor', 'doctor_name', 'date', 'start_time', 'end_time', 'is_available', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        """Validate time slot"""
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Start time must be before end time")
        
        # Check for overlapping time slots
        existing_slots = TimeSlot.objects.filter(
            doctor=data['doctor'],
            date=data['date']
        ).exclude(id=self.instance.id if self.instance else None)
        
        for slot in existing_slots:
            if slot.is_overlap(data['start_time'], data['end_time']):
                raise serializers.ValidationError("This time slot overlaps with an existing time slot")
        
        return data


class TimeSlotDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for time slots"""
    
    doctor = UserSerializer(read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'doctor', 'date', 'start_time', 'end_time', 'is_available', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
