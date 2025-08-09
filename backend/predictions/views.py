"""
Views for ML predictions and recommendations.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from accounts.permissions import IsTeacherOrAdmin, IsAdministrator
from accounts.utils import get_client_ip, create_audit_log
from accounts.models import AuditLog
from students.models import StudentProfile
from .models import (
    PredictionModel, PerformancePrediction, Recommendation, 
    ModelPerformanceMetric, PredictionFeedback
)
from .serializers import (
    PredictionModelSerializer, PerformancePredictionSerializer, RecommendationSerializer,
    ModelPerformanceMetricSerializer, PredictionFeedbackSerializer, PredictionRequestSerializer,
    BatchPredictionResultSerializer, RecommendationGenerationSerializer, ModelTrainingSerializer,
    PredictionAnalyticsSerializer
)
from .ml_service import ml_service
from .recommendation_engine import generate_recommendations
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class PredictionModelViewSet(ModelViewSet):
    """
    ViewSet for managing ML prediction models.
    """
    queryset = PredictionModel.objects.all().order_by('-created_at')
    serializer_class = PredictionModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdministrator]
    
    def perform_create(self, serializer):
        """Create model record and log action."""
        serializer.save(created_by=self.request.user)
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description=f"Created ML model: {serializer.instance.name}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a specific model."""
        try:
            model = self.get_object()
            
            # Deactivate other models
            PredictionModel.objects.filter(status=PredictionModel.Status.ACTIVE).update(
                status=PredictionModel.Status.DEPRECATED
            )
            
            # Activate this model
            model.status = PredictionModel.Status.ACTIVE
            model.save()
            
            # Reload the ML service with the new model
            ml_service.load_model(str(model.id))
            
            create_audit_log(
                user=request.user,
                action=AuditLog.Action.DATA_MODIFICATION,
                description=f"Activated ML model: {model.name}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': 'Model activated successfully'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error activating model: {str(e)}")
            return Response({'error': 'Failed to activate model'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerformancePredictionViewSet(ModelViewSet):
    """
    ViewSet for managing performance predictions.
    """
    serializer_class = PerformancePredictionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_queryset(self):
        """Filter predictions based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return PerformancePrediction.objects.all().select_related('student__user', 'model')
        elif user.is_teacher:
            return PerformancePrediction.objects.filter(
                student__enrollments__class_instance__teacher=user,
                student__enrollments__status='enrolled'
            ).distinct().select_related('student__user', 'model')
        
        return PerformancePrediction.objects.none()
    
    @action(detail=False, methods=['post'])
    def batch_predict(self, request):
        """Generate predictions for multiple students."""
        serializer = PredictionRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            student_ids = serializer.validated_data['student_ids']
            prediction_type = serializer.validated_data['prediction_type']
            
            try:
                # Get students
                students = StudentProfile.objects.filter(id__in=student_ids)
                
                if not students.exists():
                    return Response({
                        'error': 'No valid students found'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check permissions
                if request.user.is_teacher:
                    # Teachers can only predict for their students
                    allowed_students = students.filter(
                        enrollments__class_instance__teacher=request.user,
                        enrollments__status='enrolled'
                    ).distinct()
                    students = allowed_students
                
                # Get active model
                active_model = PredictionModel.objects.filter(
                    status=PredictionModel.Status.ACTIVE
                ).first()
                
                if not active_model:
                    return Response({
                        'error': 'No active ML model found'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Generate predictions
                successful_predictions = []
                failed_predictions = []
                errors = []
                
                for student in students:
                    try:
                        prediction_result = ml_service.predict_performance(student, prediction_type)
                        
                        if prediction_result:
                            # Create prediction record
                            prediction = PerformancePrediction.objects.create(
                                student=student,
                                model=active_model,
                                prediction_type=prediction_type,
                                predicted_value=prediction_result['predicted_value'],
                                confidence_score=prediction_result['confidence_score'],
                                risk_level=prediction_result['risk_level'],
                                input_features=prediction_result['input_features']
                            )
                            successful_predictions.append(prediction)
                        else:
                            failed_predictions.append(student.id)
                            errors.append(f"Failed to generate prediction for student {student.student_id}")
                    
                    except Exception as e:
                        failed_predictions.append(student.id)
                        errors.append(f"Error predicting for student {student.student_id}: {str(e)}")
                        logger.error(f"Prediction error for student {student.id}: {str(e)}")
                
                # Create audit log
                create_audit_log(
                    user=request.user,
                    action=AuditLog.Action.DATA_MODIFICATION,
                    description=f"Generated {len(successful_predictions)} predictions",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    additional_data={
                        'prediction_type': prediction_type,
                        'successful_count': len(successful_predictions),
                        'failed_count': len(failed_predictions)
                    }
                )
                
                result_data = {
                    'successful_predictions': len(successful_predictions),
                    'failed_predictions': len(failed_predictions),
                    'predictions': PerformancePredictionSerializer(successful_predictions, many=True).data,
                    'errors': errors
                }
                
                return Response(result_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Batch prediction error: {str(e)}")
                return Response({
                    'error': 'Failed to generate predictions'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecommendationViewSet(ModelViewSet):
    """
    ViewSet for managing AI-generated recommendations.
    """
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_queryset(self):
        """Filter recommendations based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return Recommendation.objects.all().select_related('student__user', 'assigned_to', 'created_by')
        elif user.is_teacher:
            return Recommendation.objects.filter(
                Q(assigned_to=user) | 
                Q(student__enrollments__class_instance__teacher=user, student__enrollments__status='enrolled')
            ).distinct().select_related('student__user', 'assigned_to', 'created_by')
        
        return Recommendation.objects.none()
    
    def perform_create(self, serializer):
        """Create recommendation and log action."""
        serializer.save(created_by=self.request.user)
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description=f"Created recommendation: {serializer.instance.title}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    @action(detail=False, methods=['post'])
    def generate_from_prediction(self, request):
        """Generate recommendations based on a prediction."""
        serializer = RecommendationGenerationSerializer(data=request.data)
        
        if serializer.is_valid():
            prediction_id = serializer.validated_data['prediction_id']
            include_resources = serializer.validated_data['include_resources']
            priority_threshold = serializer.validated_data['priority_threshold']
            
            try:
                prediction = PerformancePrediction.objects.get(id=prediction_id)
                
                # Check permissions
                if request.user.is_teacher:
                    if not prediction.student.enrollments.filter(
                        class_instance__teacher=request.user,
                        status='enrolled'
                    ).exists():
                        return Response({
                            'error': 'You do not have permission to access this prediction'
                        }, status=status.HTTP_403_FORBIDDEN)
                
                # Generate recommendations
                recommendations = generate_recommendations(
                    prediction, 
                    include_resources=include_resources,
                    priority_threshold=priority_threshold,
                    created_by=request.user
                )
                
                if recommendations:
                    return Response({
                        'message': f'Generated {len(recommendations)} recommendations',
                        'recommendations': RecommendationSerializer(recommendations, many=True).data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'message': 'No recommendations generated for this prediction'
                    }, status=status.HTTP_200_OK)
                
            except PerformancePrediction.DoesNotExist:
                return Response({
                    'error': 'Prediction not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error generating recommendations: {str(e)}")
                return Response({
                    'error': 'Failed to generate recommendations'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdministrator])
def prediction_analytics(request):
    """
    Get comprehensive analytics about predictions and model performance.
    """
    try:
        # Get date range (default to last 30 days)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Total predictions
        total_predictions = PerformancePrediction.objects.filter(
            prediction_date__gte=start_date
        ).count()
        
        # Predictions by risk level
        predictions_by_risk = PerformancePrediction.objects.filter(
            prediction_date__gte=start_date
        ).values('risk_level').annotate(count=Count('id'))
        
        risk_level_data = {item['risk_level']: item['count'] for item in predictions_by_risk}
        
        # Predictions by type
        predictions_by_type = PerformancePrediction.objects.filter(
            prediction_date__gte=start_date
        ).values('prediction_type').annotate(count=Count('id'))
        
        type_data = {item['prediction_type']: item['count'] for item in predictions_by_type}
        
        # Average confidence
        avg_confidence = PerformancePrediction.objects.filter(
            prediction_date__gte=start_date
        ).aggregate(avg_confidence=Avg('confidence_score'))['avg_confidence'] or 0
        
        # Accuracy rate (for predictions with known outcomes)
        predictions_with_outcomes = PerformancePrediction.objects.filter(
            prediction_date__gte=start_date,
            actual_outcome__isnull=False
        )
        
        if predictions_with_outcomes.exists():
            accurate_predictions = sum(
                1 for p in predictions_with_outcomes 
                if p.accuracy_if_outcome_known and p.accuracy_if_outcome_known > 0.8
            )
            accuracy_rate = accurate_predictions / predictions_with_outcomes.count()
        else:
            accuracy_rate = 0
        
        # Recent predictions
        recent_predictions = PerformancePrediction.objects.filter(
            prediction_date__gte=start_date
        ).select_related('student__user', 'model').order_by('-prediction_date')[:10]
        
        # Model performance metrics
        model_performance = ModelPerformanceMetric.objects.filter(
            evaluation_date__gte=start_date
        ).select_related('model').order_by('-evaluation_date')[:5]
        
        analytics_data = {
            'total_predictions': total_predictions,
            'predictions_by_risk_level': risk_level_data,
            'predictions_by_type': type_data,
            'average_confidence': round(avg_confidence, 4),
            'accuracy_rate': round(accuracy_rate, 4),
            'recent_predictions': PerformancePredictionSerializer(recent_predictions, many=True).data,
            'model_performance': ModelPerformanceMetricSerializer(model_performance, many=True).data
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating prediction analytics: {str(e)}")
        return Response({
            'error': 'Failed to generate analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdministrator])
def train_model(request):
    """
    Train a new ML model with uploaded data.
    """
    serializer = ModelTrainingSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            model_name = serializer.validated_data['model_name']
            description = serializer.validated_data.get('description', '')
            training_file = serializer.validated_data['training_data_file']
            target_column = serializer.validated_data['target_column']
            
            # Read training data
            if training_file.name.endswith('.csv'):
                training_data = pd.read_csv(training_file)
            elif training_file.name.endswith('.xlsx'):
                training_data = pd.read_excel(training_file)
            else:
                return Response({
                    'error': 'Unsupported file format. Please use CSV or Excel files.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate required columns
            required_columns = ml_service.feature_columns + [target_column]
            missing_columns = [col for col in required_columns if col not in training_data.columns]
            
            if missing_columns:
                return Response({
                    'error': f'Missing required columns: {missing_columns}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Train model
            model_record = ml_service.train_model(training_data, target_column, model_name)
            
            if model_record:
                model_record.description = description
                model_record.created_by = request.user
                model_record.save()
                
                create_audit_log(
                    user=request.user,
                    action=AuditLog.Action.DATA_MODIFICATION,
                    description=f"Trained new ML model: {model_name}",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    additional_data={
                        'model_id': str(model_record.id),
                        'training_data_size': model_record.training_data_size,
                        'accuracy': float(model_record.accuracy)
                    }
                )
                
                return Response({
                    'message': 'Model trained successfully',
                    'model': PredictionModelSerializer(model_record).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to train model'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return Response({
                'error': f'Training failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PredictionFeedbackViewSet(ModelViewSet):
    """
    ViewSet for managing prediction feedback.
    """
    serializer_class = PredictionFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_queryset(self):
        """Filter feedback based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return PredictionFeedback.objects.all().select_related('prediction__student__user', 'user')
        elif user.is_teacher:
            return PredictionFeedback.objects.filter(
                Q(user=user) |
                Q(prediction__student__enrollments__class_instance__teacher=user,
                  prediction__student__enrollments__status='enrolled')
            ).distinct().select_related('prediction__student__user', 'user')
        
        return PredictionFeedback.objects.none()
    
    def perform_create(self, serializer):
        """Create feedback and log action."""
        serializer.save(user=self.request.user)
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description=f"Provided feedback on prediction",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )