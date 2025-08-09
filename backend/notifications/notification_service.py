"""
Service for handling notification creation, delivery, and rule evaluation.
"""
from typing import List, Dict, Optional, Any
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from datetime import timedelta
from accounts.models import User
from students.models import StudentProfile, Grade, Attendance, BehaviorRecord
from predictions.models import PerformancePrediction, Recommendation
from .models import (
    NotificationTemplate, Notification, NotificationRule, 
    NotificationLog, NotificationPreference, AlertSubscription
)
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing notifications and alerts.
    """
    
    def create_notification(
        self,
        template: NotificationTemplate,
        recipient: User,
        context_data: Dict[str, Any] = None,
        student: Optional[StudentProfile] = None,
        channel: str = Notification.Channel.IN_APP,
        scheduled_at: Optional[timezone.datetime] = None
    ) -> Optional[Notification]:
        """
        Create a single notification.
        
        Args:
            template: NotificationTemplate instance
            recipient: User to receive the notification
            context_data: Data for template rendering
            student: Related student (optional)
            channel: Delivery channel
            scheduled_at: When to send the notification
            
        Returns:
            Created Notification instance or None if creation fails
        """
        try:
            if context_data is None:
                context_data = {}
            
            # Check user preferences
            preferences = self._get_user_preferences(recipient)
            if not self._should_send_notification(template, preferences, channel):
                logger.info(f"Notification blocked by user preferences: {recipient.email}")
                return None
            
            # Render template content
            title = self._render_template(template.title_template, context_data)
            message = self._render_template(template.message_template, context_data)
            
            # Calculate scheduled time
            if scheduled_at is None:
                scheduled_at = timezone.now() + timedelta(minutes=template.delay_minutes)
            
            # Create notification
            notification = Notification.objects.create(
                template=template,
                recipient=recipient,
                title=title,
                message=message,
                channel=channel,
                student=student,
                context_data=context_data,
                scheduled_at=scheduled_at
            )
            
            logger.info(f"Created notification: {notification.title} for {recipient.email}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None
    
    def create_bulk_notifications(
        self,
        template: NotificationTemplate,
        recipient_ids: List[str],
        student_ids: List[str] = None,
        context_data: Dict[str, Any] = None,
        channel: str = Notification.Channel.IN_APP,
        scheduled_at: Optional[timezone.datetime] = None
    ) -> List[Notification]:
        """
        Create multiple notifications at once.
        
        Args:
            template: NotificationTemplate instance
            recipient_ids: List of user IDs to receive notifications
            student_ids: List of student IDs (optional)
            context_data: Data for template rendering
            channel: Delivery channel
            scheduled_at: When to send notifications
            
        Returns:
            List of created Notification instances
        """
        notifications = []
        
        try:
            recipients = User.objects.filter(id__in=recipient_ids)
            students = None
            if student_ids:
                students = {str(s.id): s for s in StudentProfile.objects.filter(id__in=student_ids)}
            
            for recipient in recipients:
                student = None
                if students and str(recipient.id) in students:
                    student = students[str(recipient.id)]
                
                notification = self.create_notification(
                    template=template,
                    recipient=recipient,
                    context_data=context_data,
                    student=student,
                    channel=channel,
                    scheduled_at=scheduled_at
                )
                
                if notification:
                    notifications.append(notification)
            
            logger.info(f"Created {len(notifications)} bulk notifications")
            
        except Exception as e:
            logger.error(f"Error creating bulk notifications: {str(e)}")
        
        return notifications
    
    def send_pending_notifications(self) -> Dict[str, int]:
        """
        Send all pending notifications that are scheduled to be sent.
        
        Returns:
            Dictionary with send statistics
        """
        stats = {'sent': 0, 'failed': 0}
        
        try:
            # Get notifications ready to be sent
            pending_notifications = Notification.objects.filter(
                status=Notification.Status.PENDING,
                scheduled_at__lte=timezone.now()
            ).select_related('template', 'recipient')
            
            for notification in pending_notifications:
                try:
                    success = self._deliver_notification(notification)
                    if success:
                        notification.mark_as_sent()
                        stats['sent'] += 1
                    else:
                        notification.mark_as_failed("Delivery failed")
                        stats['failed'] += 1
                        
                except Exception as e:
                    notification.mark_as_failed(str(e))
                    stats['failed'] += 1
                    logger.error(f"Error sending notification {notification.id}: {str(e)}")
            
            logger.info(f"Sent {stats['sent']} notifications, {stats['failed']} failed")
            
        except Exception as e:
            logger.error(f"Error in send_pending_notifications: {str(e)}")
        
        return stats
    
    def evaluate_notification_rules(
        self, 
        students: List[StudentProfile] = None, 
        rules: List[NotificationRule] = None
    ) -> Dict[str, int]:
        """
        Evaluate notification rules and create notifications as needed.
        
        Args:
            students: List of students to evaluate (all if None)
            rules: List of rules to evaluate (active rules if None)
            
        Returns:
            Dictionary with evaluation statistics
        """
        stats = {'rules_evaluated': 0, 'students_evaluated': 0, 'notifications_created': 0}
        
        try:
            if students is None:
                students = StudentProfile.objects.all()
            
            if rules is None:
                rules = NotificationRule.objects.filter(is_active=True)
            
            stats['students_evaluated'] = len(students)
            stats['rules_evaluated'] = len(rules)
            
            for rule in rules:
                for student in students:
                    try:
                        # Check cooldown period
                        if self._is_rule_in_cooldown(rule, student):
                            continue
                        
                        # Evaluate rule condition
                        trigger_value = self._get_trigger_value(rule, student)
                        if trigger_value is None:
                            continue
                        
                        if self._evaluate_condition(rule.condition, trigger_value, rule.threshold_value):
                            # Create notifications for target roles
                            notifications_created = self._create_rule_notifications(rule, student, trigger_value)
                            stats['notifications_created'] += notifications_created
                            
                            # Log rule execution
                            NotificationLog.objects.create(
                                rule=rule,
                                student=student,
                                trigger_value=trigger_value,
                                notifications_created=notifications_created,
                                context_data={
                                    'condition': rule.condition,
                                    'threshold': float(rule.threshold_value)
                                }
                            )
                    
                    except Exception as e:
                        logger.error(f"Error evaluating rule {rule.id} for student {student.id}: {str(e)}")
            
            logger.info(f"Rule evaluation completed: {stats}")
            
        except Exception as e:
            logger.error(f"Error in evaluate_notification_rules: {str(e)}")
        
        return stats
    
    def test_notification_rule(self, rule: NotificationRule, student: StudentProfile) -> Dict[str, Any]:
        """
        Test a notification rule with a specific student.
        
        Args:
            rule: NotificationRule to test
            student: StudentProfile to test with
            
        Returns:
            Dictionary with test results
        """
        try:
            trigger_value = self._get_trigger_value(rule, student)
            condition_met = False
            
            if trigger_value is not None:
                condition_met = self._evaluate_condition(rule.condition, trigger_value, rule.threshold_value)
            
            return {
                'rule_name': rule.name,
                'student_id': student.student_id,
                'trigger_value': float(trigger_value) if trigger_value is not None else None,
                'threshold_value': float(rule.threshold_value),
                'condition': rule.condition,
                'condition_met': condition_met,
                'target_roles': rule.target_roles,
                'would_create_notifications': condition_met
            }
            
        except Exception as e:
            logger.error(f"Error testing notification rule: {str(e)}")
            return {'error': str(e)}
    
    def _get_user_preferences(self, user: User) -> Optional[NotificationPreference]:
        """Get user notification preferences."""
        try:
            return user.notification_preferences
        except NotificationPreference.DoesNotExist:
            return None
    
    def _should_send_notification(
        self, 
        template: NotificationTemplate, 
        preferences: Optional[NotificationPreference],
        channel: str
    ) -> bool:
        """Check if notification should be sent based on user preferences."""
        if preferences is None:
            return True
        
        # Check channel preferences
        if channel == Notification.Channel.EMAIL and not preferences.email_enabled:
            return False
        elif channel == Notification.Channel.SMS and not preferences.sms_enabled:
            return False
        elif channel == Notification.Channel.PUSH and not preferences.push_enabled:
            return False
        
        # Check type preferences
        type_preference_map = {
            NotificationTemplate.Type.GRADE_ALERT: preferences.grade_alerts,
            NotificationTemplate.Type.ATTENDANCE_WARNING: preferences.attendance_warnings,
            NotificationTemplate.Type.BEHAVIOR_INCIDENT: preferences.behavior_incidents,
            NotificationTemplate.Type.PREDICTION_ALERT: preferences.prediction_alerts,
            NotificationTemplate.Type.RECOMMENDATION_ASSIGNED: preferences.recommendation_assignments,
            NotificationTemplate.Type.ASSIGNMENT_DUE: preferences.assignment_reminders,
            NotificationTemplate.Type.SYSTEM_ANNOUNCEMENT: preferences.system_announcements,
        }
        
        return type_preference_map.get(template.notification_type, True)
    
    def _render_template(self, template_string: str, context_data: Dict[str, Any]) -> str:
        """Render template string with context data."""
        try:
            template = Template(template_string)
            context = Context(context_data)
            return template.render(context)
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template_string
    
    def _deliver_notification(self, notification: Notification) -> bool:
        """Deliver notification via specified channel."""
        try:
            if notification.channel == Notification.Channel.EMAIL:
                return self._send_email_notification(notification)
            elif notification.channel == Notification.Channel.SMS:
                return self._send_sms_notification(notification)
            elif notification.channel == Notification.Channel.PUSH:
                return self._send_push_notification(notification)
            else:
                # In-app notifications are always "delivered"
                notification.mark_as_delivered()
                return True
                
        except Exception as e:
            logger.error(f"Error delivering notification {notification.id}: {str(e)}")
            return False
    
    def _send_email_notification(self, notification: Notification) -> bool:
        """Send notification via email."""
        try:
            send_mail(
                subject=notification.title,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=False
            )
            notification.mark_as_delivered()
            return True
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def _send_sms_notification(self, notification: Notification) -> bool:
        """Send notification via SMS."""
        # SMS implementation would go here
        # For now, just mark as delivered
        logger.info(f"SMS notification would be sent to {notification.recipient.phone_number}")
        notification.mark_as_delivered()
        return True
    
    def _send_push_notification(self, notification: Notification) -> bool:
        """Send push notification."""
        # Push notification implementation would go here
        # For now, just mark as delivered
        logger.info(f"Push notification would be sent to {notification.recipient.email}")
        notification.mark_as_delivered()
        return True
    
    def _is_rule_in_cooldown(self, rule: NotificationRule, student: StudentProfile) -> bool:
        """Check if rule is in cooldown period for student."""
        if rule.cooldown_hours <= 0:
            return False
        
        cooldown_start = timezone.now() - timedelta(hours=rule.cooldown_hours)
        recent_execution = NotificationLog.objects.filter(
            rule=rule,
            student=student,
            triggered_at__gte=cooldown_start
        ).exists()
        
        return recent_execution
    
    def _get_trigger_value(self, rule: NotificationRule, student: StudentProfile) -> Optional[float]:
        """Get the value to compare against rule threshold."""
        try:
            if rule.trigger_type == NotificationRule.TriggerType.GRADE_THRESHOLD:
                # Get average grade percentage
                recent_grades = Grade.objects.filter(student=student).order_by('-graded_at')[:10]
                if recent_grades.exists():
                    return sum(grade.percentage for grade in recent_grades) / len(recent_grades)
                return student.gpa * 25 if student.gpa else None
            
            elif rule.trigger_type == NotificationRule.TriggerType.ATTENDANCE_RATE:
                # Calculate attendance rate
                attendance_records = Attendance.objects.filter(student=student)
                if attendance_records.exists():
                    present_count = attendance_records.filter(
                        status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
                    ).count()
                    return (present_count / attendance_records.count()) * 100
                return None
            
            elif rule.trigger_type == NotificationRule.TriggerType.BEHAVIOR_INCIDENT:
                # Count recent negative behavior incidents
                recent_incidents = BehaviorRecord.objects.filter(
                    student=student,
                    behavior_type=BehaviorRecord.Type.NEGATIVE,
                    incident_date__gte=timezone.now() - timedelta(days=30)
                ).count()
                return float(recent_incidents)
            
            elif rule.trigger_type == NotificationRule.TriggerType.PREDICTION_RISK:
                # Get latest high-risk prediction
                high_risk_prediction = PerformancePrediction.objects.filter(
                    student=student,
                    risk_level__in=[
                        PerformancePrediction.RiskLevel.HIGH,
                        PerformancePrediction.RiskLevel.CRITICAL
                    ],
                    is_active=True
                ).order_by('-prediction_date').first()
                
                if high_risk_prediction:
                    # Return risk level as numeric value
                    risk_values = {
                        PerformancePrediction.RiskLevel.LOW: 1,
                        PerformancePrediction.RiskLevel.MEDIUM: 2,
                        PerformancePrediction.RiskLevel.HIGH: 3,
                        PerformancePrediction.RiskLevel.CRITICAL: 4
                    }
                    return float(risk_values.get(high_risk_prediction.risk_level, 0))
                return 0.0
            
            elif rule.trigger_type == NotificationRule.TriggerType.RECOMMENDATION_DUE:
                # Count overdue recommendations
                overdue_recommendations = Recommendation.objects.filter(
                    student=student,
                    status__in=[Recommendation.Status.PENDING, Recommendation.Status.IN_PROGRESS],
                    due_date__lt=timezone.now()
                ).count()
                return float(overdue_recommendations)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting trigger value for rule {rule.id}: {str(e)}")
            return None
    
    def _evaluate_condition(self, condition: str, value: float, threshold: float) -> bool:
        """Evaluate rule condition."""
        if condition == NotificationRule.Condition.LESS_THAN:
            return value < threshold
        elif condition == NotificationRule.Condition.LESS_THAN_EQUAL:
            return value <= threshold
        elif condition == NotificationRule.Condition.GREATER_THAN:
            return value > threshold
        elif condition == NotificationRule.Condition.GREATER_THAN_EQUAL:
            return value >= threshold
        elif condition == NotificationRule.Condition.EQUALS:
            return abs(value - threshold) < 0.001  # Float comparison
        elif condition == NotificationRule.Condition.NOT_EQUALS:
            return abs(value - threshold) >= 0.001
        
        return False
    
    def _create_rule_notifications(
        self, 
        rule: NotificationRule, 
        student: StudentProfile, 
        trigger_value: float
    ) -> int:
        """Create notifications for rule execution."""
        notifications_created = 0
        
        try:
            # Get target users based on roles
            target_users = self._get_target_users(rule.target_roles, student)
            
            # Prepare context data
            context_data = {
                'student_name': student.user.get_full_name(),
                'student_id': student.student_id,
                'trigger_value': trigger_value,
                'threshold_value': float(rule.threshold_value),
                'rule_name': rule.name
            }
            
            # Create notifications
            for user in target_users:
                notification = self.create_notification(
                    template=rule.template,
                    recipient=user,
                    context_data=context_data,
                    student=student
                )
                
                if notification:
                    notifications_created += 1
            
        except Exception as e:
            logger.error(f"Error creating rule notifications: {str(e)}")
        
        return notifications_created
    
    def _get_target_users(self, target_roles: List[str], student: StudentProfile) -> List[User]:
        """Get users to notify based on target roles."""
        users = []
        
        try:
            for role in target_roles:
                if role == 'administrator':
                    users.extend(User.objects.filter(role=User.Role.ADMINISTRATOR))
                elif role == 'teacher':
                    # Get teachers for student's classes
                    teachers = User.objects.filter(
                        taught_classes__enrollments__student=student,
                        taught_classes__enrollments__status='enrolled'
                    ).distinct()
                    users.extend(teachers)
                elif role == 'student':
                    users.append(student.user)
                elif role == 'parent':
                    # Parent functionality would be implemented here
                    pass
            
            # Remove duplicates
            users = list(set(users))
            
        except Exception as e:
            logger.error(f"Error getting target users: {str(e)}")
        
        return users


# Global service instance
notification_service = NotificationService()