"""
URL patterns for the accounts app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.UserLogoutView.as_view(), name='user-logout'),
    
    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change-password'),
    
    # Password reset
    path('password-reset/', views.password_reset_request, name='password-reset-request'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    
    # Email verification
    path('verify-email/<uuid:token>/', views.verify_email, name='verify-email'),
    
    # Audit logs (admin only)
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-logs'),
]