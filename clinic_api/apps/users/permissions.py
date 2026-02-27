from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())


class IsDoctor(BasePermission):
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_doctor())


class IsPatient(BasePermission):
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_patient())


class IsOwner(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'patient'):
            return obj.patient == request.user
        if hasattr(obj, 'doctor'):
            return obj.doctor == request.user
        return False


class IsAdminOrReadOnly(BasePermission):
    
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())


class IsOwnerOrAdmin(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin():
            return True
        user = request.user
        if hasattr(obj, 'user') and obj.user == user:
            return True
        if hasattr(obj, 'patient') and obj.patient == user:
            return True
        if hasattr(obj, 'doctor') and obj.doctor == user:
            return True
        return False
