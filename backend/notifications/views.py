"""
Views for notifications and alerts system.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveUpdateAPIView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from accounts.permissions import IsTeacherOrAdmin, IsAdministrator
from accounts.utils import get_client_ip, create_audit_log
from accounts.models import AuditLog
from students.models import StudentProfile
from .models import (
    NotificationTemplate, Notification, NotificationPreference, 
    NotificationRule, NotificationLog, AlertSubscription
)
from .serializers import (
    NotificationTemplateSerializer, NotificationSerializer, NotificationPreferenceSerializer,
    NotificationRuleSerializer, NotificationLogSerializer, AlertSubscriptionSerializer,
    NotificationSummarySerializer, BulkNotificationSerializer, NotificationMarkReadSerializer
)
from .notification_service import notification_service
import logging

logger = logging.getLogger(__name__)


class NotificationTemplateViewSet(ModelViewSet):
    """
    ViewSet for managing notification templates.
    """
    queryset = NotificationTemplate.objects.all().order_by('name')
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdministrator]
    
    def perform_create(self, serializer):
        """Create template and log action."""
        serializer.save()
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description=f"Created notification template: {serializer.instance.name}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )


class NotificationViewSet(ModelViewSet):
    """
    ViewSet for managing notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter notifications based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return Notification.objects.all().select_related('template', 'recipient', 'student__user')
        elif user.is_teacher:
            # Teachers see notifications for their students and notifications assigned to them
            return Notification.objects.filter(
                Q(recipient=user) |
                Q(student__enrollments__class_instance__teacher=user,
                  student__enrollments__status='enrolled')
            ).distinct().select_related('template', 'recipient', 'student__user')
        else:
            # Students and others see only their own notifications
            return Notification.objects.filter(
                recipient=user
            ).select_related('template', 'student__user')
    
    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """Mark multiple notifications as read."""
        serializer = NotificationMarkReadSerializer(data=request.data)
        
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            
            # Get notifications that belong to the user
            notifications = self.get_queryset().filter(
                id__in=notification_ids,
                status__in=[Notification.Status.SENT, Notification.Status.DELIVERED]
            )
            
            marked_count = 0
            for notification in notifications:
                notification.mark_as_read()
                marked_count += 1
            
            return Response({
                'message': f'Marked {marked_count} notifications as read'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get notification summary for the user."""
        try:
            queryset = self.get_queryset()
            
            # Calculate summary statistics
            total_notifications = queryset.count()
            unread_count = queryset.filter(
                status__in=[Notification.Status.SENT, Notification.Status.DELIVERED]
            ).count()
            
            # Notifications by type
            notifications_by_type = dict(
                queryset.values('template__notification_type').annotate(
                    count=Count('id')
                ).values_list('template__notification_type', 'count')
            )
            
            # Notifications by status
            notifications_by_status = dict(
                queryset.values('status').annotate(
                    count=Count('id')
                ).values_list('status', 'count')
            )
            
            # Recent notifications (last 10)
            recent_notifications = queryset.order_by('-created_at')[:10]
            
            summary_data = {
                'total_notifications': total_notifications,
                'unread_count': unread_count,
                'notifications_by_type': notifications_by_type,
                'notifications_by_status': notifications_by_status,
                'recent_notifications': NotificationSerializer(recent_notifications, many=True).data
            }
            
            return Response(summary_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating notification summary: {str(e)}")
            return Response({
                'error': 'Failed to generate notification summary'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple notifications at once."""
        if not request.user.is_administrator:
            return Response({
                'error': 'Only administrators can create bulk notifications'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = BulkNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                template_id = serializer.validated_data['template_id']
                recipient_ids = serializer.validated_data['recipient_ids']
                student_ids = serializer.validated_data.get('student_ids', [])
                context_data = serializer.validated_data.get('context_data', {})
                scheduled_at = serializer.validated_data.get('scheduled_at', timezone.now())
                channel = serializer.validated_data['channel']
                
                # Get template
                try:
                    template = NotificationTemplate.objects.get(id=template_id)
                except NotificationTemplate.DoesNotExist:
                    return Response({
                        'error': 'Notification template not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Create notifications
                created_notifications = notification_service.create_bulk_notifications(
                    template=template,
                    recipient_ids=recipient_ids,
                    student_ids=student_ids,
                    context_data=context_data,
                    scheduled_at=scheduled_at,
                    channel=channel
                )
                
                create_audit_log(
                    user=request.user,
                    action=AuditLog.Action.DATA_MODIFICATION,
                    description=f"Created {len(created_notifications)} bulk notifications",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    additional_data={
                        'template_id': str(template_id),
                        'notification_count': len(created_notifications)
                    }
                )
                
                return Response({
                    'message': f'Created {len(created_notifications)} notifications',
                    'notifications': NotificationSerializer(created_notifications, many=True).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Error creating bulk notifications: {str(e)}")
                return Response({
                    'error': 'Failed to create bulk notifications'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationPreferenceView(RetrieveUpdateAPIView):
    """
    View for managing user notification preferences.
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get or create notification preferences for the user."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preferences
    
    def perform_update(self, serializer):
        """Update preferences and log action."""
        serializer.save()
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.PROFILE_UPDATE,
            description="Updated notification preferences",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )


class NotificationRuleViewSet(ModelViewSet):
    """
    ViewSet for managing notification rules.
    """
    queryset = NotificationRule.objects.all().select_related('template').order_by('name')
    serializer_class = NotificationRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdministrator]
    
    def perform_create(self, serializer):
        """Create rule and log action."""
        serializer.save()
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description=f"Created notification rule: {serializer.instance.name}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    @action(detail=True, methods=['post'])
    def test_rule(self, request, pk=None):
        """Test a notification rule with sample data."""
        try:
            rule = self.get_object()
            
            # Get a sample student for testing
            sample_student = StudentProfile.objects.first()
            if not sample_student:
                return Response({
                    'error': 'No students available for testing'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Test the rule
            test_result = notification_service.test_notification_rule(rule, sample_student)
            
            return Response({
                'message': 'Rule test completed',
                'result': test_result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error testing notification rule: {str(e)}")
            return Response({
                'error': 'Failed to test notification rule'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlertSubscriptionViewSet(ModelViewSet):
    """
    ViewSet for managing alert subscriptions.
    """
    serializer_class = AlertSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_queryset(self):
        """Filter subscriptions based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return AlertSubscription.objects.all().select_related('user', 'student__user')
        elif user.is_teacher:
            # Teachers can manage subscriptions for their students
            return AlertSubscription.objects.filter(
                Q(user=user) |
                Q(student__enrollments__class_instance__teacher=user,
                  student__enrollments__status='enrolled')
            ).distinct().select_related('user', 'student__user')
        
        return AlertSubscription.objects.filter(user=user).select_related('student__user')
    
    def perform_create(self, serializer):
        """Create subscription and log action."""
        serializer.save(user=self.request.user)
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description=f"Created alert subscription for student {serializer.instance.student.student_id}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdministrator])
def trigger_notification_rules(request):
    """
    Manually trigger notification rule evaluation.
    """
    try:
        # Get optional student filter
        student_id = request.data.get('student_id')
        rule_id = request.data.get('rule_id')
        
        if student_id:
            try:
                student = StudentProfile.objects.get(id=student_id)
                students = [student]
            except StudentProfile.DoesNotExist:
                return Response({
                    'error': 'Student not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            students = StudentProfile.objects.all()
        
        if rule_id:
            try:
                rule = NotificationRule.objects.get(id=rule_id)
                rules = [rule]
            except NotificationRule.DoesNotExist:
                return Response({
                    'error': 'Notification rule not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            rules = NotificationRule.objects.filter(is_active=True)
        
        # Trigger rule evaluation
        results = notification_service.evaluate_notification_rules(students, rules)
        
        create_audit_log(
            user=request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description="Manually triggered notification rule evaluation",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            additional_data={
                'students_evaluated': len(students),
                'rules_evaluated': len(rules),
                'notifications_created': results.get('notifications_created', 0)
            }
        )
        
        return Response({
            'message': 'Notification rules triggered successfully',
            'results': results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error triggering notification rules: {str(e)}")
        return Response({
            'error': 'Failed to trigger notification rules'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdministrator])
def notification_analytics(request):
    """
    Get analytics about notification system performance.
    """
    try:
        # Get date range (default to last 30 days)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Total notifications
        total_notifications = Notification.objects.filter(created_at__gte=start_date).count()
        
        # Delivery statistics
        delivery_stats = {
            'sent': Notification.objects.filter(
                created_at__gte=start_date,
                status=Notification.Status.SENT
            ).count(),
            'delivered': Notification.objects.filter(
                created_at__gte=start_date,
                status=Notification.Status.DELIVERED
            ).count(),
            'read': Notification.objects.filter(
                created_at__gte=start_date,
                status=Notification.Status.READ
            ).count(),
            'failed': Notification.objects.filter(
                created_at__gte=start_date,
                status=Notification.Status.FAILED
            ).count(),
        }
        
        # Channel distribution
        channel_stats = dict(
            Notification.objects.filter(
                created_at__gte=start_date
            ).values('channel').annotate(count=Count('id')).values_list('channel', 'count')
        )
        
        # Type distribution
        type_stats = dict(
            Notification.objects.filter(
                created_at__gte=start_date
            ).values('template__notification_type').annotate(
                count=Count('id')
            ).values_list('template__notification_type', 'count')
        )
        
        # Rule execution statistics
        rule_executions = NotificationLog.objects.filter(
            triggered_at__gte=start_date
        ).count()
        
        # Most active rules
        active_rules = NotificationLog.objects.filter(
            triggered_at__gte=start_date
        ).values('rule__name').annotate(
            executions=Count('id'),
            notifications_created=Count('notifications_created')
        ).order_by('-executions')[:5]
        
        analytics_data = {
            'total_notifications': total_notifications,
            'delivery_stats': delivery_stats,
            'channel_stats': channel_stats,
            'type_stats': type_stats,
            'rule_executions': rule_executions,
            'active_rules': list(active_rules),
            'delivery_rate': round(
                (delivery_stats['delivered'] / total_notifications * 100) if total_notifications > 0 else 0, 2
            ),
            'read_rate': round(
                (delivery_stats['read'] / total_notifications * 100) if total_notifications > 0 else 0, 2
            )
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating notification analytics: {str(e)}")
        return Response({
            'error': 'Failed to generate notification analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)