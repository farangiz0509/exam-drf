from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from clinic_api.apps.appointments.models import Appointment
from clinic_api.apps.appointments.serializers import (
    AppointmentSerializer,
    AppointmentDetailSerializer,
    AppointmentStatusUpdateSerializer,
)
from clinic_api.apps.users.permissions import IsOwnerOrAdmin, IsDoctor, IsPatient, IsAdmin


class AppointmentViewSet(viewsets.ModelViewSet):
    

    queryset = (
        Appointment.objects
        .select_related('doctor', 'patient', 'timeslot')
        .all()
    )
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, filters.OrderingFilter]
    search_fields = ['doctor__first_name', 'doctor__last_name', 'patient__first_name', 'patient__last_name']
    ordering_fields = ['created_at', 'timeslot__date']
    
    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        params = self.request.query_params
        doctor = params.get('doctor')
        date = params.get('date')
        status = params.get('status')
        if doctor:
            qs = qs.filter(doctor_id=doctor)
        if date:
            qs = qs.filter(timeslot__date=date)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_permissions(self):
        
        perms = [permissions.IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            perms.append(IsOwnerOrAdmin())
        elif self.action in ['create']:
            perms.append(IsPatient())
        else:
            perms.append(IsOwnerOrAdmin())
        return perms

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return AppointmentStatusUpdateSerializer
        if self.action in ['retrieve']:
            return AppointmentDetailSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_admin():
            return qs
        if user.is_doctor():
            return qs.filter(doctor=user)
        if user.is_patient():
            return qs.filter(patient=user)
        return qs.none()

    def perform_create(self, serializer):
        
        serializer.save(patient=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_patient() and instance.patient != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.is_patient():
            return Response({'detail': 'Patients cannot modify appointments.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
