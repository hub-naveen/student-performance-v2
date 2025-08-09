"""
URL patterns for the notifications app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'templates', views.NotificationTemplateViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'rules', views.NotificationRuleViewSet)
router.register(r'subscriptions', views.AlertSubscriptionViewSet, basename='alert-subscription')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # User preferences
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
    
    # System management
    path('trigger-rules/', views.trigger_notification_rules, name='trigger-notification-rules'),
    path('analytics/', views.notification_analytics, name='notification-analytics'),
]