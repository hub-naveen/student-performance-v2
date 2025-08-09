"""
AI-powered recommendation engine for generating student interventions.
"""
from typing import List, Dict, Optional
from django.utils import timezone
from .models import PerformancePrediction, Recommendation
from students.models import StudentProfile, Grade, Attendance, BehaviorRecord
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Engine for generating personalized recommendations based on predictions.
    """
    
    def __init__(self):
        self.recommendation_templates = {
            # Academic Support Recommendations
            'low_gpa': {
                'title': 'Academic Support Program',
                'description': 'Student shows signs of academic struggle and would benefit from additional support.',
                'category': Recommendation.Category.ACADEMIC,
                'priority': Recommendation.Priority.HIGH,
                'suggested_actions': [
                    'Enroll in tutoring program',
                    'Schedule weekly check-ins with academic advisor',
                    'Provide study skills workshop',
                    'Consider reduced course load if appropriate'
                ],
                'resources_needed': [
                    'Tutoring services',
                    'Academic advisor time',
                    'Study materials',
                    'Quiet study space'
                ],
                'success_metrics': [
                    'Improved GPA by 0.5 points',
                    'Increased assignment completion rate',
                    'Better test scores'
                ]
            },
            
            # Attendance Interventions
            'poor_attendance': {
                'title': 'Attendance Improvement Plan',
                'description': 'Student has concerning attendance patterns that may impact academic success.',
                'category': Recommendation.Category.ATTENDANCE,
                'priority': Recommendation.Priority.HIGH,
                'suggested_actions': [
                    'Meet with student and parents to discuss attendance',
                    'Identify barriers to regular attendance',
                    'Implement attendance monitoring system',
                    'Provide transportation assistance if needed'
                ],
                'resources_needed': [
                    'Counselor time',
                    'Parent communication system',
                    'Transportation resources',
                    'Attendance tracking tools'
                ],
                'success_metrics': [
                    'Attendance rate above 90%',
                    'Reduced unexcused absences',
                    'Improved punctuality'
                ]
            },
            
            # Behavioral Support
            'behavioral_concerns': {
                'title': 'Behavioral Support Intervention',
                'description': 'Student exhibits behavioral patterns that may interfere with learning.',
                'category': Recommendation.Category.BEHAVIORAL,
                'priority': Recommendation.Priority.MEDIUM,
                'suggested_actions': [
                    'Implement positive behavior support plan',
                    'Provide social-emotional learning resources',
                    'Schedule regular counseling sessions',
                    'Train teachers on behavior management strategies'
                ],
                'resources_needed': [
                    'School counselor',
                    'Behavior specialist',
                    'SEL curriculum materials',
                    'Teacher training time'
                ],
                'success_metrics': [
                    'Reduced disciplinary incidents',
                    'Improved classroom behavior ratings',
                    'Better peer relationships'
                ]
            },
            
            # Engagement Strategies
            'low_engagement': {
                'title': 'Student Engagement Enhancement',
                'description': 'Student shows low engagement levels that may affect academic performance.',
                'category': Recommendation.Category.ENGAGEMENT,
                'priority': Recommendation.Priority.MEDIUM,
                'suggested_actions': [
                    'Identify student interests and strengths',
                    'Connect learning to real-world applications',
                    'Encourage participation in extracurricular activities',
                    'Implement project-based learning opportunities'
                ],
                'resources_needed': [
                    'Interest assessment tools',
                    'Project materials',
                    'Activity program access',
                    'Mentor assignment'
                ],
                'success_metrics': [
                    'Increased class participation',
                    'Higher assignment quality',
                    'Participation in school activities'
                ]
            },
            
            # Dropout Prevention
            'dropout_risk': {
                'title': 'Dropout Prevention Program',
                'description': 'Student is at high risk of dropping out and needs intensive intervention.',
                'category': Recommendation.Category.COUNSELING,
                'priority': Recommendation.Priority.URGENT,
                'suggested_actions': [
                    'Assign dedicated case manager',
                    'Develop individualized success plan',
                    'Provide career counseling and goal setting',
                    'Connect with community support services',
                    'Consider alternative education options'
                ],
                'resources_needed': [
                    'Case manager',
                    'Career counselor',
                    'Community partnerships',
                    'Alternative program options',
                    'Family support services'
                ],
                'success_metrics': [
                    'Student remains enrolled',
                    'Improved academic performance',
                    'Clear post-graduation plan',
                    'Increased family engagement'
                ]
            },
            
            # Tutoring Support
            'subject_specific_help': {
                'title': 'Subject-Specific Tutoring',
                'description': 'Student needs additional support in specific academic areas.',
                'category': Recommendation.Category.TUTORING,
                'priority': Recommendation.Priority.MEDIUM,
                'suggested_actions': [
                    'Arrange peer or professional tutoring',
                    'Provide additional practice materials',
                    'Use technology-assisted learning tools',
                    'Schedule regular progress check-ins'
                ],
                'resources_needed': [
                    'Qualified tutors',
                    'Supplementary materials',
                    'Learning software/apps',
                    'Progress tracking system'
                ],
                'success_metrics': [
                    'Improved subject-specific grades',
                    'Better understanding of concepts',
                    'Increased confidence in subject area'
                ]
            }
        }
    
    def analyze_student_needs(self, student: StudentProfile) -> List[str]:
        """
        Analyze student data to identify areas needing intervention.
        
        Args:
            student: StudentProfile instance
            
        Returns:
            List of recommendation template keys
        """
        needs = []
        
        try:
            # Check GPA
            if student.gpa and student.gpa < 2.5:
                needs.append('low_gpa')
            
            # Check attendance
            attendance_records = Attendance.objects.filter(student=student)
            if attendance_records.exists():
                present_count = attendance_records.filter(
                    status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
                ).count()
                attendance_rate = present_count / attendance_records.count()
                
                if attendance_rate < 0.85:
                    needs.append('poor_attendance')
            
            # Check behavior
            recent_behavior = BehaviorRecord.objects.filter(
                student=student,
                incident_date__gte=timezone.now() - timezone.timedelta(days=30)
            )
            
            negative_behaviors = recent_behavior.filter(
                behavior_type=BehaviorRecord.Type.NEGATIVE
            ).count()
            
            if negative_behaviors > 3:
                needs.append('behavioral_concerns')
            
            # Check engagement (based on assignment completion)
            recent_grades = Grade.objects.filter(
                student=student,
                graded_at__gte=timezone.now() - timezone.timedelta(days=30)
            )
            
            if recent_grades.exists():
                avg_score = sum(grade.percentage for grade in recent_grades) / len(recent_grades)
                if avg_score < 70:
                    needs.append('low_engagement')
                    needs.append('subject_specific_help')
            
            # Check for dropout risk factors
            risk_factors = 0
            
            if student.gpa and student.gpa < 2.0:
                risk_factors += 2
            if attendance_records.exists() and (present_count / attendance_records.count()) < 0.8:
                risk_factors += 2
            if negative_behaviors > 5:
                risk_factors += 1
            if student.family_income_bracket == 'low':
                risk_factors += 1
            if student.has_learning_disability:
                risk_factors += 1
            
            if risk_factors >= 4:
                needs.append('dropout_risk')
            
        except Exception as e:
            logger.error(f"Error analyzing student needs for {student.id}: {str(e)}")
        
        return needs
    
    def generate_recommendations(
        self, 
        prediction: PerformancePrediction, 
        include_resources: bool = True,
        priority_threshold: str = Recommendation.Priority.MEDIUM,
        created_by: Optional[User] = None
    ) -> List[Recommendation]:
        """
        Generate recommendations based on a performance prediction.
        
        Args:
            prediction: PerformancePrediction instance
            include_resources: Whether to include resource requirements
            priority_threshold: Minimum priority level for recommendations
            created_by: User creating the recommendations
            
        Returns:
            List of created Recommendation instances
        """
        recommendations = []
        
        try:
            student = prediction.student
            
            # Analyze student needs
            identified_needs = self.analyze_student_needs(student)
            
            # Add prediction-specific needs
            if prediction.risk_level == PerformancePrediction.RiskLevel.CRITICAL:
                if prediction.prediction_type == PerformancePrediction.PredictionType.DROPOUT_RISK:
                    identified_needs.append('dropout_risk')
                else:
                    identified_needs.append('low_gpa')
            elif prediction.risk_level == PerformancePrediction.RiskLevel.HIGH:
                identified_needs.extend(['low_gpa', 'subject_specific_help'])
            
            # Remove duplicates
            identified_needs = list(set(identified_needs))
            
            # Generate recommendations
            for need in identified_needs:
                if need in self.recommendation_templates:
                    template = self.recommendation_templates[need]
                    
                    # Check priority threshold
                    priority_order = [
                        Recommendation.Priority.LOW,
                        Recommendation.Priority.MEDIUM,
                        Recommendation.Priority.HIGH,
                        Recommendation.Priority.URGENT
                    ]
                    
                    if priority_order.index(template['priority']) >= priority_order.index(priority_threshold):
                        # Create recommendation
                        recommendation = Recommendation.objects.create(
                            student=student,
                            prediction=prediction,
                            title=template['title'],
                            description=self._personalize_description(template['description'], student, prediction),
                            category=template['category'],
                            priority=template['priority'],
                            suggested_actions=template['suggested_actions'] if include_resources else [],
                            resources_needed=template['resources_needed'] if include_resources else [],
                            success_metrics=template['success_metrics'],
                            estimated_duration=self._estimate_duration(template['category']),
                            created_by=created_by,
                            due_date=self._calculate_due_date(template['priority'])
                        )
                        
                        recommendations.append(recommendation)
                        
                        logger.info(f"Created recommendation: {recommendation.title} for student {student.student_id}")
            
        except Exception as e:
            logger.error(f"Error generating recommendations for prediction {prediction.id}: {str(e)}")
        
        return recommendations
    
    def _personalize_description(self, description: str, student: StudentProfile, prediction: PerformancePrediction) -> str:
        """
        Personalize recommendation description with student-specific information.
        """
        personalized = description
        
        # Add prediction-specific context
        if prediction.confidence_score > 0.8:
            personalized += f" Our AI model predicts this with {prediction.confidence_score:.1%} confidence."
        
        # Add risk level context
        if prediction.risk_level == PerformancePrediction.RiskLevel.CRITICAL:
            personalized += " This is a high-priority intervention requiring immediate attention."
        
        return personalized
    
    def _estimate_duration(self, category: str) -> str:
        """
        Estimate duration based on recommendation category.
        """
        duration_map = {
            Recommendation.Category.ACADEMIC: "4-6 weeks",
            Recommendation.Category.BEHAVIORAL: "6-8 weeks",
            Recommendation.Category.ATTENDANCE: "2-4 weeks",
            Recommendation.Category.ENGAGEMENT: "3-5 weeks",
            Recommendation.Category.COUNSELING: "8-12 weeks",
            Recommendation.Category.TUTORING: "4-8 weeks",
            Recommendation.Category.EXTRACURRICULAR: "Ongoing"
        }
        
        return duration_map.get(category, "4-6 weeks")
    
    def _calculate_due_date(self, priority: str) -> timezone.datetime:
        """
        Calculate due date based on priority level.
        """
        now = timezone.now()
        
        if priority == Recommendation.Priority.URGENT:
            return now + timezone.timedelta(days=3)
        elif priority == Recommendation.Priority.HIGH:
            return now + timezone.timedelta(days=7)
        elif priority == Recommendation.Priority.MEDIUM:
            return now + timezone.timedelta(days=14)
        else:  # LOW
            return now + timezone.timedelta(days=30)


# Global instance
recommendation_engine = RecommendationEngine()


def generate_recommendations(
    prediction: PerformancePrediction,
    include_resources: bool = True,
    priority_threshold: str = Recommendation.Priority.MEDIUM,
    created_by: Optional[User] = None
) -> List[Recommendation]:
    """
    Convenience function to generate recommendations.
    """
    return recommendation_engine.generate_recommendations(
        prediction, include_resources, priority_threshold, created_by
    )