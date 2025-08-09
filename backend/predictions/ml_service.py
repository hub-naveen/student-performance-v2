"""
Machine Learning service for student performance predictions.
"""
import joblib
import pandas as pd
import numpy as np
from django.conf import settings
from django.utils import timezone
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging
import os
from typing import Dict, List, Tuple, Optional
from .models import PredictionModel, PerformancePrediction, ModelPerformanceMetric
from students.models import StudentProfile, Grade, Attendance, BehaviorRecord

logger = logging.getLogger(__name__)


class MLPredictionService:
    """
    Service class for handling ML predictions and model management.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = [
            'gpa', 'attendance_rate', 'assignment_completion_rate',
            'behavior_score', 'participation_score', 'grade_level_numeric',
            'parental_education_numeric', 'family_income_numeric',
            'has_learning_disability', 'receives_free_lunch'
        ]
    
    def load_model(self, model_id: str = None) -> bool:
        """
        Load the ML model and scaler from disk.
        
        Args:
            model_id: Specific model ID to load, if None loads the active model
            
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            if model_id:
                model_record = PredictionModel.objects.get(id=model_id)
            else:
                model_record = PredictionModel.objects.filter(
                    status=PredictionModel.Status.ACTIVE
                ).order_by('-created_at').first()
            
            if not model_record:
                logger.error("No active model found")
                return False
            
            # Load model and scaler
            if os.path.exists(model_record.model_file_path):
                self.model = joblib.load(model_record.model_file_path)
                logger.info(f"Loaded model: {model_record.name} v{model_record.version}")
            else:
                logger.error(f"Model file not found: {model_record.model_file_path}")
                return False
            
            if model_record.scaler_file_path and os.path.exists(model_record.scaler_file_path):
                self.scaler = joblib.load(model_record.scaler_file_path)
                logger.info(f"Loaded scaler for model: {model_record.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def prepare_student_features(self, student: StudentProfile) -> Dict:
        """
        Prepare feature vector for a student.
        
        Args:
            student: StudentProfile instance
            
        Returns:
            Dict: Feature dictionary for the student
        """
        try:
            # Calculate GPA
            recent_grades = Grade.objects.filter(student=student).order_by('-graded_at')[:20]
            if recent_grades.exists():
                gpa = sum(grade.percentage for grade in recent_grades) / len(recent_grades) / 25.0  # Convert to 4.0 scale
            else:
                gpa = student.gpa or 2.5  # Default GPA
            
            # Calculate attendance rate
            attendance_records = Attendance.objects.filter(student=student)
            if attendance_records.exists():
                present_count = attendance_records.filter(
                    status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
                ).count()
                attendance_rate = present_count / attendance_records.count()
            else:
                attendance_rate = 0.95  # Default attendance rate
            
            # Calculate assignment completion rate
            total_assignments = Grade.objects.filter(student=student).count()
            if total_assignments > 0:
                assignment_completion_rate = total_assignments / max(total_assignments, 1)
            else:
                assignment_completion_rate = 0.8  # Default completion rate
            
            # Calculate behavior score
            behavior_records = BehaviorRecord.objects.filter(student=student)
            positive_behaviors = behavior_records.filter(behavior_type=BehaviorRecord.Type.POSITIVE).count()
            negative_behaviors = behavior_records.filter(behavior_type=BehaviorRecord.Type.NEGATIVE).count()
            
            if positive_behaviors + negative_behaviors > 0:
                behavior_score = positive_behaviors / (positive_behaviors + negative_behaviors)
            else:
                behavior_score = 0.8  # Default behavior score
            
            # Encode categorical variables
            grade_level_numeric = int(student.grade_level) if student.grade_level.isdigit() else 10
            
            parental_education_map = {
                'none': 0, 'primary': 1, 'secondary': 2, 'some_college': 3,
                'bachelors': 4, 'masters': 5, 'doctorate': 6
            }
            parental_education_numeric = parental_education_map.get(student.parental_education_level, 2)
            
            family_income_map = {'low': 0, 'middle': 1, 'high': 2}
            family_income_numeric = family_income_map.get(student.family_income_bracket, 1)
            
            features = {
                'gpa': gpa,
                'attendance_rate': attendance_rate,
                'assignment_completion_rate': assignment_completion_rate,
                'behavior_score': behavior_score,
                'participation_score': 0.8,  # Default participation score
                'grade_level_numeric': grade_level_numeric,
                'parental_education_numeric': parental_education_numeric,
                'family_income_numeric': family_income_numeric,
                'has_learning_disability': 1 if student.has_learning_disability else 0,
                'receives_free_lunch': 1 if student.receives_free_lunch else 0,
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features for student {student.id}: {str(e)}")
            return {}
    
    def predict_performance(self, student: StudentProfile, prediction_type: str = 'grade') -> Optional[Dict]:
        """
        Make a performance prediction for a student.
        
        Args:
            student: StudentProfile instance
            prediction_type: Type of prediction to make
            
        Returns:
            Dict: Prediction results or None if prediction fails
        """
        try:
            if not self.model:
                if not self.load_model():
                    logger.error("Failed to load model for prediction")
                    return None
            
            # Prepare features
            features = self.prepare_student_features(student)
            if not features:
                logger.error(f"Failed to prepare features for student {student.id}")
                return None
            
            # Create feature vector
            feature_vector = np.array([[features[col] for col in self.feature_columns]])
            
            # Scale features if scaler is available
            if self.scaler:
                feature_vector = self.scaler.transform(feature_vector)
            
            # Make prediction
            if hasattr(self.model, 'predict_proba'):
                # Classification model
                prediction_proba = self.model.predict_proba(feature_vector)[0]
                predicted_value = np.argmax(prediction_proba)
                confidence_score = np.max(prediction_proba)
            else:
                # Regression model
                predicted_value = self.model.predict(feature_vector)[0]
                confidence_score = 0.8  # Default confidence for regression
            
            # Determine risk level
            if prediction_type == 'dropout':
                if predicted_value > 0.7:
                    risk_level = PerformancePrediction.RiskLevel.CRITICAL
                elif predicted_value > 0.5:
                    risk_level = PerformancePrediction.RiskLevel.HIGH
                elif predicted_value > 0.3:
                    risk_level = PerformancePrediction.RiskLevel.MEDIUM
                else:
                    risk_level = PerformancePrediction.RiskLevel.LOW
            else:
                # Grade prediction
                if predicted_value < 2.0:
                    risk_level = PerformancePrediction.RiskLevel.CRITICAL
                elif predicted_value < 2.5:
                    risk_level = PerformancePrediction.RiskLevel.HIGH
                elif predicted_value < 3.0:
                    risk_level = PerformancePrediction.RiskLevel.MEDIUM
                else:
                    risk_level = PerformancePrediction.RiskLevel.LOW
            
            return {
                'predicted_value': float(predicted_value),
                'confidence_score': float(confidence_score),
                'risk_level': risk_level,
                'input_features': features
            }
            
        except Exception as e:
            logger.error(f"Error making prediction for student {student.id}: {str(e)}")
            return None
    
    def batch_predict(self, students: List[StudentProfile], prediction_type: str = 'grade') -> List[Dict]:
        """
        Make predictions for multiple students.
        
        Args:
            students: List of StudentProfile instances
            prediction_type: Type of prediction to make
            
        Returns:
            List[Dict]: List of prediction results
        """
        predictions = []
        
        for student in students:
            prediction = self.predict_performance(student, prediction_type)
            if prediction:
                prediction['student_id'] = student.id
                predictions.append(prediction)
        
        return predictions
    
    def train_model(self, training_data: pd.DataFrame, target_column: str, model_name: str) -> Optional[PredictionModel]:
        """
        Train a new ML model with provided data.
        
        Args:
            training_data: DataFrame with training data
            target_column: Name of the target column
            model_name: Name for the new model
            
        Returns:
            PredictionModel: Created model record or None if training fails
        """
        try:
            # Prepare features and target
            X = training_data[self.feature_columns]
            y = training_data[target_column]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if y.dtype == 'object' else None
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            if y.dtype == 'object' or len(y.unique()) <= 10:
                # Classification
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted')
                recall = recall_score(y_test, y_pred, average='weighted')
                f1 = f1_score(y_test, y_pred, average='weighted')
            else:
                # Regression
                model = GradientBoostingRegressor(n_estimators=100, random_state=42)
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                
                # Calculate metrics (convert to classification-like metrics)
                accuracy = 1 - np.mean(np.abs(y_test - y_pred) / np.maximum(np.abs(y_test), 1))
                precision = accuracy  # For regression, use same as accuracy
                recall = accuracy
                f1 = accuracy
            
            # Save model and scaler
            model_dir = settings.BASE_DIR / 'ml_models'
            model_dir.mkdir(exist_ok=True)
            
            model_filename = f"{model_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.joblib"
            scaler_filename = f"{model_name}_scaler_{timezone.now().strftime('%Y%m%d_%H%M%S')}.joblib"
            
            model_path = model_dir / model_filename
            scaler_path = model_dir / scaler_filename
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Create model record
            model_record = PredictionModel.objects.create(
                name=model_name,
                version=f"1.{timezone.now().strftime('%Y%m%d')}",
                description=f"Trained on {len(training_data)} samples",
                model_file_path=str(model_path),
                scaler_file_path=str(scaler_path),
                status=PredictionModel.Status.ACTIVE,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                training_data_size=len(training_data),
                features_used=self.feature_columns,
                hyperparameters=model.get_params() if hasattr(model, 'get_params') else {}
            )
            
            logger.info(f"Successfully trained model: {model_name} with accuracy: {accuracy:.4f}")
            return model_record
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return None
    
    def evaluate_model_performance(self, model_id: str, test_data: pd.DataFrame, target_column: str) -> Optional[ModelPerformanceMetric]:
        """
        Evaluate model performance on test data.
        
        Args:
            model_id: ID of the model to evaluate
            test_data: DataFrame with test data
            target_column: Name of the target column
            
        Returns:
            ModelPerformanceMetric: Performance metric record or None if evaluation fails
        """
        try:
            model_record = PredictionModel.objects.get(id=model_id)
            
            # Load model
            model = joblib.load(model_record.model_file_path)
            scaler = None
            if model_record.scaler_file_path:
                scaler = joblib.load(model_record.scaler_file_path)
            
            # Prepare test data
            X_test = test_data[self.feature_columns]
            y_test = test_data[target_column]
            
            if scaler:
                X_test = scaler.transform(X_test)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            if hasattr(model, 'predict_proba'):
                # Classification
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted')
                recall = recall_score(y_test, y_pred, average='weighted')
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                # Calculate confusion matrix components
                from sklearn.metrics import confusion_matrix
                cm = confusion_matrix(y_test, y_pred)
                if cm.shape == (2, 2):
                    tn, fp, fn, tp = cm.ravel()
                else:
                    # Multi-class, use macro averages
                    tp = np.diag(cm).sum()
                    fp = cm.sum(axis=0) - np.diag(cm)
                    fn = cm.sum(axis=1) - np.diag(cm)
                    tn = cm.sum() - (fp + fn + tp)
                    tp, fp, fn, tn = int(tp), int(fp.sum()), int(fn.sum()), int(tn)
            else:
                # Regression - convert to classification-like metrics
                accuracy = 1 - np.mean(np.abs(y_test - y_pred) / np.maximum(np.abs(y_test), 1))
                precision = accuracy
                recall = accuracy
                f1 = accuracy
                tp, tn, fp, fn = len(y_test), 0, 0, 0  # Simplified for regression
            
            # Create performance metric record
            metric_record = ModelPerformanceMetric.objects.create(
                model=model_record,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                true_positives=tp,
                true_negatives=tn,
                false_positives=fp,
                false_negatives=fn,
                test_data_size=len(test_data)
            )
            
            logger.info(f"Model evaluation completed. Accuracy: {accuracy:.4f}")
            return metric_record
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return None


# Global instance
ml_service = MLPredictionService()