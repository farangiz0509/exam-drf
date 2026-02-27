from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from clinic_api.apps.doctors.models import TimeSlot
from clinic_api.apps.users.serializers import TimeSlotSerializer, TimeSlotDetailSerializer
from clinic_api.apps.users.permissions import IsDoctor, IsAdmin, IsOwner


class TimeSlotViewSet(viewsets.ModelViewSet):

    

    queryset = TimeSlot.objects.select_related('doctor').all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['date', 'doctor__first_name', 'doctor__last_name']
    ordering_fields = ['date', 'start_time']
    
    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        params = self.request.query_params
        date = params.get('date')
        available = params.get('is_available')
        if date:
            qs = qs.filter(date=date)
        if available is not None:
            if available.lower() in ['true', '1']:
                qs = qs.filter(is_available=True)
            elif available.lower() in ['false', '0']:
                qs = qs.filter(is_available=False)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsDoctor()]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return TimeSlotDetailSerializer
        return TimeSlotSerializer

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_admin():
            return qs
        if user.is_doctor():
            return qs.filter(doctor=user)
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user, is_available=True)

    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(TimeSlotSerializer(page, many=True).data)
        return Response(TimeSlotSerializer(qs, many=True).data)
