"""
Serializers for prediction-related models.
"""
from rest_framework import serializers
from .models import (
    PredictionModel, PerformancePrediction, Recommendation, 
    ModelPerformanceMetric, PredictionFeedback
)
from students.serializers import StudentProfileSerializer
from accounts.serializers import UserProfileSerializer


class PredictionModelSerializer(serializers.ModelSerializer):
    """
    Serializer for ML prediction models.
    """
    created_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = PredictionModel
        fields = [
            'id', 'name', 'version', 'description', 'status',
            'accuracy', 'precision', 'recall', 'f1_score',
            'training_data_size', 'features_used', 'hyperparameters',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'accuracy', 'precision', 
            'recall', 'f1_score', 'training_data_size'
        ]


class PerformancePredictionSerializer(serializers.ModelSerializer):
    """
    Serializer for performance predictions.
    """
    student = StudentProfileSerializer(read_only=True)
    model = PredictionModelSerializer(read_only=True)
    accuracy_if_outcome_known = serializers.ReadOnlyField()
    
    class Meta:
        model = PerformancePrediction
        fields = [
            'id', 'student', 'model', 'prediction_type', 'predicted_value',
            'confidence_score', 'risk_level', 'input_features', 'prediction_date',
            'is_active', 'actual_outcome', 'outcome_date', 'accuracy_if_outcome_known'
        ]
        read_only_fields = [
            'id', 'prediction_date', 'accuracy_if_outcome_known'
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for AI-generated recommendations.
    """
    student = StudentProfileSerializer(read_only=True)
    prediction = PerformancePredictionSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    created_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'student', 'prediction', 'title', 'description', 'category',
            'priority', 'status', 'suggested_actions', 'resources_needed',
            'estimated_duration', 'success_metrics', 'assigned_to', 'created_by',
            'created_at', 'updated_at', 'due_date', 'completed_at',
            'effectiveness_rating', 'effectiveness_notes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModelPerformanceMetricSerializer(serializers.ModelSerializer):
    """
    Serializer for model performance metrics.
    """
    model = PredictionModelSerializer(read_only=True)
    
    class Meta:
        model = ModelPerformanceMetric
        fields = [
            'id', 'model', 'accuracy', 'precision', 'recall', 'f1_score',
            'true_positives', 'true_negatives', 'false_positives', 'false_negatives',
            'evaluation_date', 'test_data_size', 'notes'
        ]
        read_only_fields = ['id', 'evaluation_date']


class PredictionFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for prediction feedback.
    """
    prediction = PerformancePredictionSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = PredictionFeedback
        fields = [
            'id', 'prediction', 'user', 'feedback_type', 'rating', 
            'comments', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PredictionRequestSerializer(serializers.Serializer):
    """
    Serializer for prediction requests.
    """
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    prediction_type = serializers.ChoiceField(
        choices=PerformancePrediction.PredictionType.choices,
        default=PerformancePrediction.PredictionType.GRADE_PREDICTION
    )


class BatchPredictionResultSerializer(serializers.Serializer):
    """
    Serializer for batch prediction results.
    """
    successful_predictions = serializers.IntegerField()
    failed_predictions = serializers.IntegerField()
    predictions = PerformancePredictionSerializer(many=True)
    errors = serializers.ListField(child=serializers.CharField(), required=False)


class RecommendationGenerationSerializer(serializers.Serializer):
    """
    Serializer for recommendation generation requests.
    """
    prediction_id = serializers.UUIDField()
    include_resources = serializers.BooleanField(default=True)
    priority_threshold = serializers.ChoiceField(
        choices=Recommendation.Priority.choices,
        default=Recommendation.Priority.MEDIUM
    )


class ModelTrainingSerializer(serializers.Serializer):
    """
    Serializer for model training requests.
    """
    model_name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    training_data_file = serializers.FileField()
    target_column = serializers.CharField(max_length=50)
    test_size = serializers.FloatField(default=0.2, min_value=0.1, max_value=0.5)


class PredictionAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for prediction analytics data.
    """
    total_predictions = serializers.IntegerField()
    predictions_by_risk_level = serializers.DictField()
    predictions_by_type = serializers.DictField()
    average_confidence = serializers.FloatField()
    accuracy_rate = serializers.FloatField()
    recent_predictions = PerformancePredictionSerializer(many=True)
    model_performance = ModelPerformanceMetricSerializer(many=True)