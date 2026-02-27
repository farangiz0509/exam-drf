from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only admin users can access"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())


class IsDoctor(BasePermission):
    """Only doctor users can access"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_doctor())


class IsPatient(BasePermission):
    """Only patient users can access"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_patient())


class IsOwner(BasePermission):
    """Check if user is the owner of the object"""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'patient'):
            return obj.patient == request.user
        if hasattr(obj, 'doctor'):
            return obj.doctor == request.user
        return False


class IsAdminOrReadOnly(BasePermission):
    """Allow admin users or read-only access"""
    
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())


class IsOwnerOrAdmin(BasePermission):
    """Check if user is the owner or admin"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin():
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'patient'):
            return obj.patient == request.user
        if hasattr(obj, 'doctor'):
            return obj.doctor == request.user
        return False
