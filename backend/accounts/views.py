"""
Authentication and user management views.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from django.contrib.auth import login, logout
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from oauth2_provider.models import Application, AccessToken
from .models import User, EmailVerificationToken, PasswordResetToken, UserSession, AuditLog
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer, AuditLogSerializer
)
from .permissions import IsOwnerOrAdmin, IsAdministrator
from .utils import get_client_ip, create_audit_log
import uuid
from datetime import timedelta


class UserRegistrationView(APIView):
    """
    User registration endpoint with email verification.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def post(self, request):
        """Register a new user and send email verification."""
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Create email verification token
                    verification_token = EmailVerificationToken.objects.create(
                        user=user,
                        expires_at=timezone.now() + timedelta(hours=24)
                    )
                    
                    # Send verification email
                    self._send_verification_email(user, verification_token)
                    
                    # Create audit log
                    create_audit_log(
                        user=user,
                        action=AuditLog.Action.DATA_MODIFICATION,
                        description="User account created",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    return Response({
                        'message': 'User registered successfully. Please check your email for verification.',
                        'user_id': user.id
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                return Response({
                    'error': 'Registration failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_verification_email(self, user, token):
        """Send email verification email."""
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token.token}"
        
        send_mail(
            subject='Verify Your Email - Student Performance System',
            message=f'Please click the following link to verify your email: {verification_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )


class UserLoginView(APIView):
    """
    User login endpoint with OAuth2 token generation.
    """
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    def post(self, request):
        """Authenticate user and return OAuth2 tokens."""
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            try:
                # Create OAuth2 application if it doesn't exist
                application, created = Application.objects.get_or_create(
                    name="Student Performance App",
                    defaults={
                        'user': None,
                        'client_type': Application.CLIENT_CONFIDENTIAL,
                        'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
                    }
                )
                
                # Create access token
                access_token = AccessToken.objects.create(
                    user=user,
                    application=application,
                    token=str(uuid.uuid4()),
                    expires=timezone.now() + timedelta(seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']),
                    scope='read write'
                )
                
                # Create user session
                UserSession.objects.create(
                    user=user,
                    session_key=request.session.session_key or str(uuid.uuid4()),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Update last login IP
                user.last_login_ip = get_client_ip(request)
                user.save(update_fields=['last_login_ip'])
                
                # Create audit log
                create_audit_log(
                    user=user,
                    action=AuditLog.Action.LOGIN,
                    description="User logged in successfully",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                return Response({
                    'access_token': access_token.token,
                    'token_type': 'Bearer',
                    'expires_in': settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'],
                    'user': UserProfileSerializer(user).data
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': 'Login failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """
    User logout endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Logout user and invalidate tokens."""
        try:
            # Get authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Delete access token
                AccessToken.objects.filter(token=token).delete()
            
            # Deactivate user sessions
            UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action=AuditLog.Action.LOGOUT,
                description="User logged out",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Logout failed. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(RetrieveUpdateAPIView):
    """
    User profile view for retrieving and updating profile information.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        """Update user profile and create audit log."""
        serializer.save()
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.PROFILE_UPDATE,
            description="User profile updated",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )


class PasswordChangeView(APIView):
    """
    Password change endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Change user password."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            
            # Invalidate all existing tokens
            AccessToken.objects.filter(user=request.user).delete()
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action=AuditLog.Action.PASSWORD_CHANGE,
                description="Password changed successfully",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='3/m', method='POST')
def password_reset_request(request):
    """Request password reset token."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Create password reset token
            reset_token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            
            # Send reset email
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"
            
            send_mail(
                subject='Password Reset - Student Performance System',
                message=f'Please click the following link to reset your password: {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
        except User.DoesNotExist:
            # Don't reveal if email exists
            pass
        
        return Response({
            'message': 'If the email exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """Confirm password reset with token."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
            
            if reset_token.is_expired():
                return Response({
                    'error': 'Password reset token has expired.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            # Invalidate all existing tokens
            AccessToken.objects.filter(user=user).delete()
            
            # Create audit log
            create_audit_log(
                user=user,
                action=AuditLog.Action.PASSWORD_CHANGE,
                description="Password reset via token",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'message': 'Password reset successfully.'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'error': 'Invalid password reset token.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email(request, token):
    """Verify user email with token."""
    try:
        verification_token = EmailVerificationToken.objects.get(token=token, is_used=False)
        
        if verification_token.is_expired():
            return Response({
                'error': 'Email verification token has expired.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify email
        user = verification_token.user
        user.is_email_verified = True
        user.save()
        
        # Mark token as used
        verification_token.is_used = True
        verification_token.save()
        
        return Response({
            'message': 'Email verified successfully.'
        }, status=status.HTTP_200_OK)
        
    except EmailVerificationToken.DoesNotExist:
        return Response({
            'error': 'Invalid email verification token.'
        }, status=status.HTTP_400_BAD_REQUEST)


class AuditLogListView(ListAPIView):
    """
    List audit logs for administrators.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdministrator]
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # Filter by user if specified
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action if specified
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset