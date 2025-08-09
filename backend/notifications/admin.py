"""
Admin configuration for the notifications app.
"""
from django.contrib import admin
from .models import (
    NotificationTemplate, Notification, NotificationPreference, 
    NotificationRule, NotificationLog, AlertSubscription
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for NotificationTemplate.
    """
    list_display = ['name', 'notification_type', 'priority', 'is_active', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_active', 'send_email', 'send_sms', 'send_push']
    search_fields = ['name', 'title_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'notification_type', 'priority', 'is_active')
        }),
        ('Content Templates', {
            'fields': ('title_template', 'message_template')
        }),
        ('Delivery Settings', {
            'fields': ('send_email', 'send_sms', 'send_push', 'delay_minutes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification.
    """
    list_display = ['title', 'recipient', 'channel', 'status', 'created_at', 'sent_at']
    list_filter = ['channel', 'status', 'created_at', 'template__notification_type']
    search_fields = ['title', 'recipient__email', 'recipient__first_name', 'recipient__last_name']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'read_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('template', 'recipient', 'student', 'title', 'message')
        }),
        ('Delivery Details', {
            'fields': ('channel', 'status', 'scheduled_at')
        }),
        ('Context Data', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('delivery_attempts', 'last_error')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'delivered_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Notifications should be created programmatically


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Admin interface for NotificationPreference.
    """
    list_display = ['user', 'email_enabled', 'sms_enabled', 'push_enabled', 'daily_digest', 'weekly_digest']
    list_filter = ['email_enabled', 'sms_enabled', 'push_enabled', 'daily_digest', 'weekly_digest']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channel Preferences', {
            'fields': ('email_enabled', 'sms_enabled', 'push_enabled')
        }),
        ('Type Preferences', {
            'fields': (
                'grade_alerts', 'attendance_warnings', 'behavior_incidents',
                'prediction_alerts', 'recommendation_assignments', 'assignment_reminders',
                'system_announcements'
            )
        }),
        ('Timing Preferences', {
            'fields': ('quiet_hours_start', 'quiet_hours_end', 'timezone')
        }),
        ('Digest Preferences', {
            'fields': ('daily_digest', 'weekly_digest')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    """
    Admin interface for NotificationRule.
    """
    list_display = ['name', 'trigger_type', 'condition', 'threshold_value', 'is_active', 'cooldown_hours']
    list_filter = ['trigger_type', 'condition', 'is_active', 'template__notification_type']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Trigger Configuration', {
            'fields': ('trigger_type', 'condition', 'threshold_value')
        }),
        ('Target Configuration', {
            'fields': ('template', 'target_roles')
        }),
        ('Timing', {
            'fields': ('cooldown_hours',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """
    Admin interface for NotificationLog.
    """
    list_display = ['rule', 'student', 'trigger_value', 'notifications_created', 'triggered_at']
    list_filter = ['triggered_at', 'rule__trigger_type']
    search_fields = ['rule__name', 'student__student_id', 'student__user__email']
    readonly_fields = ['triggered_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AlertSubscription)
class AlertSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for AlertSubscription.
    """
    list_display = ['user', 'student', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'student__student_id', 'student__user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'student', 'is_active')
        }),
        ('Notification Types', {
            'fields': ('notification_types',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )