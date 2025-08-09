"""
Models for ML predictions and recommendations.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import StudentProfile
from accounts.models import User
import uuid


class PredictionModel(models.Model):
    """
    Model to track different ML models and their versions.
    """
    
    class Status(models.TextChoices):
        TRAINING = 'training', 'Training'
        ACTIVE = 'active', 'Active'
        DEPRECATED = 'deprecated', 'Deprecated'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    model_file_path = models.CharField(max_length=500)
    scaler_file_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRAINING)
    accuracy = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    precision = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    recall = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    f1_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    training_data_size = models.PositiveIntegerField(null=True, blank=True)
    features_used = models.JSONField(default=list)
    hyperparameters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_models')
    
    class Meta:
        db_table = 'prediction_models'
        unique_together = ['name', 'version']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.status})"


class PerformancePrediction(models.Model):
    """
    Model to store individual student performance predictions.
    """
    
    class RiskLevel(models.TextChoices):
        LOW = 'low', 'Low Risk'
        MEDIUM = 'medium', 'Medium Risk'
        HIGH = 'high', 'High Risk'
        CRITICAL = 'critical', 'Critical Risk'
    
    class PredictionType(models.TextChoices):
        GRADE_PREDICTION = 'grade', 'Grade Prediction'
        DROPOUT_RISK = 'dropout', 'Dropout Risk'
        GRADUATION_LIKELIHOOD = 'graduation', 'Graduation Likelihood'
        SUBJECT_PERFORMANCE = 'subject', 'Subject Performance'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='predictions')
    model = models.ForeignKey(PredictionModel, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.CharField(max_length=20, choices=PredictionType.choices)
    
    # Prediction results
    predicted_value = models.DecimalField(max_digits=6, decimal_places=3)
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices)
    
    # Input features used for prediction
    input_features = models.JSONField(default=dict)
    
    # Metadata
    prediction_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    actual_outcome = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    outcome_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'performance_predictions'
        indexes = [
            models.Index(fields=['student', 'prediction_type']),
            models.Index(fields=['prediction_date']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.prediction_type} - {self.risk_level}"
    
    @property
    def accuracy_if_outcome_known(self):
        """Calculate prediction accuracy if actual outcome is known."""
        if self.actual_outcome is not None:
            error = abs(float(self.predicted_value) - float(self.actual_outcome))
            max_possible_error = max(float(self.predicted_value), float(self.actual_outcome))
            if max_possible_error > 0:
                return 1 - (error / max_possible_error)
        return None


class Recommendation(models.Model):
    """
    Model to store AI-generated recommendations for students.
    """
    
    class Category(models.TextChoices):
        ACADEMIC = 'academic', 'Academic Support'
        BEHAVIORAL = 'behavioral', 'Behavioral Intervention'
        ATTENDANCE = 'attendance', 'Attendance Improvement'
        ENGAGEMENT = 'engagement', 'Student Engagement'
        COUNSELING = 'counseling', 'Counseling Services'
        TUTORING = 'tutoring', 'Tutoring Support'
        EXTRACURRICULAR = 'extracurricular', 'Extracurricular Activities'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low Priority'
        MEDIUM = 'medium', 'Medium Priority'
        HIGH = 'high', 'High Priority'
        URGENT = 'urgent', 'Urgent'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        DISMISSED = 'dismissed', 'Dismissed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='recommendations')
    prediction = models.ForeignKey(
        PerformancePrediction, 
        on_delete=models.CASCADE, 
        related_name='recommendations',
        null=True, 
        blank=True
    )
    
    # Recommendation details
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Implementation details
    suggested_actions = models.JSONField(default=list)
    resources_needed = models.JSONField(default=list)
    estimated_duration = models.CharField(max_length=100, blank=True)  # e.g., "2-4 weeks"
    success_metrics = models.JSONField(default=list)
    
    # Assignment and tracking
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_recommendations'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_recommendations'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Effectiveness tracking
    effectiveness_rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    effectiveness_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'recommendations'
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['category', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.title} ({self.priority})"


class ModelPerformanceMetric(models.Model):
    """
    Model to track ML model performance over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(PredictionModel, on_delete=models.CASCADE, related_name='performance_metrics')
    
    # Performance metrics
    accuracy = models.DecimalField(max_digits=5, decimal_places=4)
    precision = models.DecimalField(max_digits=5, decimal_places=4)
    recall = models.DecimalField(max_digits=5, decimal_places=4)
    f1_score = models.DecimalField(max_digits=5, decimal_places=4)
    
    # Additional metrics
    true_positives = models.PositiveIntegerField()
    true_negatives = models.PositiveIntegerField()
    false_positives = models.PositiveIntegerField()
    false_negatives = models.PositiveIntegerField()
    
    # Metadata
    evaluation_date = models.DateTimeField(auto_now_add=True)
    test_data_size = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'model_performance_metrics'
        indexes = [
            models.Index(fields=['model', 'evaluation_date']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - Accuracy: {self.accuracy} ({self.evaluation_date.date()})"


class PredictionFeedback(models.Model):
    """
    Model to collect feedback on prediction accuracy from teachers and administrators.
    """
    
    class FeedbackType(models.TextChoices):
        ACCURACY = 'accuracy', 'Accuracy Feedback'
        USEFULNESS = 'usefulness', 'Usefulness Feedback'
        SUGGESTION = 'suggestion', 'Improvement Suggestion'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prediction = models.ForeignKey(PerformancePrediction, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prediction_feedback')
    
    feedback_type = models.CharField(max_length=20, choices=FeedbackType.choices)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'prediction_feedback'
        unique_together = ['prediction', 'user', 'feedback_type']
        indexes = [
            models.Index(fields=['prediction']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Feedback on {self.prediction} by {self.user.get_full_name()}"