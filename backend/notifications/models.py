"""
Models for notifications and alerts system.
"""
from django.db import models
from django.utils import timezone
from accounts.models import User
from students.models import StudentProfile
import uuid


class NotificationTemplate(models.Model):
    """
    Templates for different types of notifications.
    """
    
    class Type(models.TextChoices):
        GRADE_ALERT = 'grade_alert', 'Grade Alert'
        ATTENDANCE_WARNING = 'attendance_warning', 'Attendance Warning'
        BEHAVIOR_INCIDENT = 'behavior_incident', 'Behavior Incident'
        PREDICTION_ALERT = 'prediction_alert', 'Prediction Alert'
        RECOMMENDATION_ASSIGNED = 'recommendation_assigned', 'Recommendation Assigned'
        ASSIGNMENT_DUE = 'assignment_due', 'Assignment Due'
        PARENT_CONFERENCE = 'parent_conference', 'Parent Conference'
        SYSTEM_ANNOUNCEMENT = 'system_announcement', 'System Announcement'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=30, choices=Type.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Template content
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Delivery settings
    send_email = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    send_push = models.BooleanField(default=True)
    
    # Timing settings
    delay_minutes = models.PositiveIntegerField(default=0, help_text="Delay before sending notification")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        indexes = [
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.notification_type})"


class Notification(models.Model):
    """
    Individual notification instances.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        READ = 'read', 'Read'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    class Channel(models.TextChoices):
        IN_APP = 'in_app', 'In-App'
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'
        PUSH = 'push', 'Push Notification'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Delivery details
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    
    # Related objects
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Metadata
    context_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery tracking
    delivery_attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['student']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} -> {self.recipient.email} ({self.status})"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if self.status != self.Status.READ:
            self.status = self.Status.READ
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
    
    def mark_as_sent(self):
        """Mark notification as sent."""
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_delivered(self):
        """Mark notification as delivered."""
        self.status = self.Status.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_failed(self, error_message: str = ""):
        """Mark notification as failed."""
        self.status = self.Status.FAILED
        self.last_error = error_message
        self.delivery_attempts += 1
        self.save(update_fields=['status', 'last_error', 'delivery_attempts'])


class NotificationPreference(models.Model):
    """
    User preferences for notifications.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    
    # Type preferences
    grade_alerts = models.BooleanField(default=True)
    attendance_warnings = models.BooleanField(default=True)
    behavior_incidents = models.BooleanField(default=True)
    prediction_alerts = models.BooleanField(default=True)
    recommendation_assignments = models.BooleanField(default=True)
    assignment_reminders = models.BooleanField(default=True)
    system_announcements = models.BooleanField(default=True)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Digest preferences
    daily_digest = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"


class NotificationRule(models.Model):
    """
    Rules for automatic notification triggering.
    """
    
    class TriggerType(models.TextChoices):
        GRADE_THRESHOLD = 'grade_threshold', 'Grade Below Threshold'
        ATTENDANCE_RATE = 'attendance_rate', 'Attendance Rate Below Threshold'
        BEHAVIOR_INCIDENT = 'behavior_incident', 'Behavior Incident Reported'
        PREDICTION_RISK = 'prediction_risk', 'High Risk Prediction'
        ASSIGNMENT_OVERDUE = 'assignment_overdue', 'Assignment Overdue'
        RECOMMENDATION_DUE = 'recommendation_due', 'Recommendation Due Soon'
    
    class Condition(models.TextChoices):
        LESS_THAN = 'lt', 'Less Than'
        LESS_THAN_EQUAL = 'lte', 'Less Than or Equal'
        GREATER_THAN = 'gt', 'Greater Than'
        GREATER_THAN_EQUAL = 'gte', 'Greater Than or Equal'
        EQUALS = 'eq', 'Equals'
        NOT_EQUALS = 'ne', 'Not Equals'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Trigger configuration
    trigger_type = models.CharField(max_length=30, choices=TriggerType.choices)
    condition = models.CharField(max_length=5, choices=Condition.choices)
    threshold_value = models.DecimalField(max_digits=10, decimal_places=3)
    
    # Target configuration
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='rules')
    target_roles = models.JSONField(default=list, help_text="List of user roles to notify")
    
    # Status and timing
    is_active = models.BooleanField(default=True)
    cooldown_hours = models.PositiveIntegerField(default=24, help_text="Hours to wait before triggering again for same student")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_rules'
        indexes = [
            models.Index(fields=['trigger_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.trigger_type})"


class NotificationLog(models.Model):
    """
    Log of notification rule executions.
    """
    rule = models.ForeignKey(NotificationRule, on_delete=models.CASCADE, related_name='execution_logs')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='notification_logs')
    
    # Execution details
    triggered_at = models.DateTimeField(auto_now_add=True)
    trigger_value = models.DecimalField(max_digits=10, decimal_places=3)
    notifications_created = models.PositiveIntegerField(default=0)
    
    # Context
    context_data = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'notification_logs'
        indexes = [
            models.Index(fields=['rule', 'student']),
            models.Index(fields=['triggered_at']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} triggered for {self.student.user.get_full_name()}"


class AlertSubscription(models.Model):
    """
    User subscriptions to specific types of alerts for specific students.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alert_subscriptions')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='alert_subscriptions')
    
    # Subscription settings
    notification_types = models.JSONField(default=list, help_text="List of notification types to subscribe to")
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alert_subscriptions'
        unique_together = ['user', 'student']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['student']),
        ]
    
    def __str__(self):
        return f"{self.user.email} subscribed to alerts for {self.student.user.get_full_name()}"