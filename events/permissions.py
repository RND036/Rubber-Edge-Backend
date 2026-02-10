from rest_framework import permissions


class IsOfficerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow officers to create/edit events.
    Farmers can only read events.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'officer'
        )
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            hasattr(request.user, 'role') and
            request.user.role == 'officer' and
            obj.created_by == request.user
        )


class IsOfficer(permissions.BasePermission):
    """
    Permission to check if user is an officer
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'officer'
        )


class IsFarmer(permissions.BasePermission):
    """
    Permission to check if user is a farmer
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'farmer'
        )


class IsOwnerOrOfficer(permissions.BasePermission):
    """
    Permission to check if user is the owner or an officer
    """
    
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'role') and request.user.role == 'officer':
            return True
        
        if hasattr(obj, 'farmer'):
            return obj.farmer == request.user
        
        return False
