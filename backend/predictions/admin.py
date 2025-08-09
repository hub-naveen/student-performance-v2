"""
Admin configuration for the predictions app.
"""
from django.contrib import admin
from .models import (
    PredictionModel, PerformancePrediction, Recommendation, 
    ModelPerformanceMetric, PredictionFeedback
)


@admin.register(PredictionModel)
class PredictionModelAdmin(admin.ModelAdmin):
    """
    Admin interface for PredictionModel.
    """
    list_display = ['name', 'version', 'status', 'accuracy', 'created_at', 'created_by']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'version', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'version', 'description', 'status')
        }),
        ('File Paths', {
            'fields': ('model_file_path', 'scaler_file_path')
        }),
        ('Performance Metrics', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score', 'training_data_size')
        }),
        ('Configuration', {
            'fields': ('features_used', 'hyperparameters'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PerformancePrediction)
class PerformancePredictionAdmin(admin.ModelAdmin):
    """
    Admin interface for PerformancePrediction.
    """
    list_display = ['student', 'prediction_type', 'predicted_value', 'confidence_score', 'risk_level', 'prediction_date']
    list_filter = ['prediction_type', 'risk_level', 'is_active', 'prediction_date']
    search_fields = ['student__student_id', 'student__user__email']
    readonly_fields = ['prediction_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'model', 'prediction_type', 'is_active')
        }),
        ('Prediction Results', {
            'fields': ('predicted_value', 'confidence_score', 'risk_level')
        }),
        ('Input Data', {
            'fields': ('input_features',),
            'classes': ('collapse',)
        }),
        ('Outcome Tracking', {
            'fields': ('actual_outcome', 'outcome_date')
        }),
        ('Metadata', {
            'fields': ('prediction_date',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """
    Admin interface for Recommendation.
    """
    list_display = ['title', 'student', 'category', 'priority', 'status', 'assigned_to', 'due_date']
    list_filter = ['category', 'priority', 'status', 'created_at']
    search_fields = ['title', 'student__student_id', 'student__user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'prediction', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status')
        }),
        ('Implementation Details', {
            'fields': ('suggested_actions', 'resources_needed', 'estimated_duration', 'success_metrics'),
            'classes': ('collapse',)
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by', 'due_date')
        }),
        ('Tracking', {
            'fields': ('completed_at', 'effectiveness_rating', 'effectiveness_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ModelPerformanceMetric)
class ModelPerformanceMetricAdmin(admin.ModelAdmin):
    """
    Admin interface for ModelPerformanceMetric.
    """
    list_display = ['model', 'accuracy', 'precision', 'recall', 'f1_score', 'evaluation_date']
    list_filter = ['evaluation_date', 'model__name']
    readonly_fields = ['evaluation_date']
    
    fieldsets = (
        ('Model Information', {
            'fields': ('model', 'evaluation_date', 'test_data_size')
        }),
        ('Performance Metrics', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score')
        }),
        ('Confusion Matrix', {
            'fields': ('true_positives', 'true_negatives', 'false_positives', 'false_negatives')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PredictionFeedback)
class PredictionFeedbackAdmin(admin.ModelAdmin):
    """
    Admin interface for PredictionFeedback.
    """
    list_display = ['prediction', 'user', 'feedback_type', 'rating', 'created_at']
    list_filter = ['feedback_type', 'rating', 'created_at']
    search_fields = ['prediction__student__student_id', 'user__email']
    readonly_fields = ['created_at']
    
    def has_change_permission(self, request, obj=None):
        # Allow users to edit their own feedback
        if obj and obj.user == request.user:
            return True
        return super().has_change_permission(request, obj)