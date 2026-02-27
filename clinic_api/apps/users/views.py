from rest_framework import viewsets, generics, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from clinic_api.apps.users.models import User
from clinic_api.apps.users.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
)
from clinic_api.apps.users.permissions import IsAdmin, IsOwner, IsAdminOrReadOnly

from clinic_api.apps.doctors.models import TimeSlot


class UserRegistrationView(generics.CreateAPIView):

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save()


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all().order_by('-created_at')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'role']
    ordering_fields = ['created_at', 'username']

    def get_permissions(self):
        if self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = User.objects.filter(role='doctor', is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'doctor_profile__specialization']
    ordering_fields = ['first_name', 'last_name']

    @action(detail=True, methods=['get'], url_path='timeslots')
    def timeslots(self, request, pk=None):

        doctor = self.get_object()
        qs = (
            TimeSlot.objects
            .filter(doctor=doctor, is_available=True)
            .select_related('doctor')
            .order_by('date', 'start_time')
        )

        page = self.paginate_queryset(qs)
        from clinic_api.apps.users.serializers import TimeSlotSerializer
        if page is not None:
            return self.get_paginated_response(TimeSlotSerializer(page, many=True).data)
        return Response(TimeSlotSerializer(qs, many=True).data)
