"""
Serializers for notification-related models.
"""
from rest_framework import serializers
from .models import (
    NotificationTemplate, Notification, NotificationPreference, 
    NotificationRule, NotificationLog, AlertSubscription
)
from accounts.serializers import UserProfileSerializer
from students.serializers import StudentProfileSerializer


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for notification templates.
    """
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'priority', 'title_template',
            'message_template', 'send_email', 'send_sms', 'send_push',
            'delay_minutes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications.
    """
    template = NotificationTemplateSerializer(read_only=True)
    recipient = UserProfileSerializer(read_only=True)
    student = StudentProfileSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'template', 'recipient', 'title', 'message', 'channel',
            'status', 'student', 'context_data', 'created_at', 'scheduled_at',
            'sent_at', 'delivered_at', 'read_at', 'delivery_attempts', 'last_error'
        ]
        read_only_fields = [
            'id', 'created_at', 'sent_at', 'delivered_at', 'delivery_attempts', 'last_error'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for notification preferences.
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'user', 'email_enabled', 'sms_enabled', 'push_enabled',
            'grade_alerts', 'attendance_warnings', 'behavior_incidents',
            'prediction_alerts', 'recommendation_assignments', 'assignment_reminders',
            'system_announcements', 'quiet_hours_start', 'quiet_hours_end',
            'timezone', 'daily_digest', 'weekly_digest', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NotificationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for notification rules.
    """
    template = NotificationTemplateSerializer(read_only=True)
    
    class Meta:
        model = NotificationRule
        fields = [
            'id', 'name', 'description', 'trigger_type', 'condition',
            'threshold_value', 'template', 'target_roles', 'is_active',
            'cooldown_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    """
    Serializer for notification logs.
    """
    rule = NotificationRuleSerializer(read_only=True)
    student = StudentProfileSerializer(read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'rule', 'student', 'triggered_at', 'trigger_value',
            'notifications_created', 'context_data'
        ]
        read_only_fields = ['id', 'triggered_at']


class AlertSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for alert subscriptions.
    """
    user = UserProfileSerializer(read_only=True)
    student = StudentProfileSerializer(read_only=True)
    
    class Meta:
        model = AlertSubscription
        fields = [
            'id', 'user', 'student', 'notification_types', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSummarySerializer(serializers.Serializer):
    """
    Serializer for notification summary data.
    """
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_status = serializers.DictField()
    recent_notifications = NotificationSerializer(many=True)


class BulkNotificationSerializer(serializers.Serializer):
    """
    Serializer for bulk notification creation.
    """
    template_id = serializers.UUIDField()
    recipient_ids = serializers.ListField(child=serializers.UUIDField())
    student_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    context_data = serializers.DictField(required=False, default=dict)
    scheduled_at = serializers.DateTimeField(required=False)
    channel = serializers.ChoiceField(
        choices=Notification.Channel.choices,
        default=Notification.Channel.IN_APP
    )


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    notification_ids = serializers.ListField(child=serializers.UUIDField())