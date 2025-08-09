"""
URL patterns for the predictions app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'models', views.PredictionModelViewSet)
router.register(r'predictions', views.PerformancePredictionViewSet, basename='prediction')
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')
router.register(r'feedback', views.PredictionFeedbackViewSet, basename='prediction-feedback')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Analytics and reporting
    path('analytics/', views.prediction_analytics, name='prediction-analytics'),
    
    # Model training
    path('train-model/', views.train_model, name='train-model'),
]