from django.contrib import admin
from django.urls import path
from rest_framework.routers import DefaultRouter

# view imports
from clinic_api.apps.users.views import (
    UserViewSet,
    UserRegistrationView,
    DoctorViewSet,
)
from clinic_api.apps.doctors.views import TimeSlotViewSet
from clinic_api.apps.appointments.views import AppointmentViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('admin/', admin.site.urls),
    # auth
    path('auth/register/', UserRegistrationView.as_view(), name='auth-register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', UserViewSet.as_view({'get': 'me'}), name='auth-me'),
]

urlpatterns += router.urls

