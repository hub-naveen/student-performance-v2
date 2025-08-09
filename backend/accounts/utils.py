"""
Utility functions for the accounts app.
"""
from django.http import HttpRequest
from .models import AuditLog


def get_client_ip(request: HttpRequest) -> str:
    """
    Get the client IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, action, description, ip_address, user_agent='', additional_data=None):
    """
    Create an audit log entry.
    """
    if additional_data is None:
        additional_data = {}
    
    AuditLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        additional_data=additional_data
    )