"""
Custom permissions for role-based access control.
"""
from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of an object or administrators to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Administrators have full access
        if request.user.is_administrator:
            return True
        
        # Users can only access their own objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For User objects, check if it's the same user
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class IsStudent(permissions.BasePermission):
    """
    Permission to only allow students to access.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student


class IsTeacher(permissions.BasePermission):
    """
    Permission to only allow teachers to access.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher


class IsAdministrator(permissions.BasePermission):
    """
    Permission to only allow administrators to access.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_administrator


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Permission to only allow teachers or administrators to access.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.is_teacher or request.user.is_administrator)
        )


class IsStudentOrTeacherOrAdmin(permissions.BasePermission):
    """
    Permission to allow students, teachers, or administrators to access.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.is_student or request.user.is_teacher or request.user.is_administrator)
        )