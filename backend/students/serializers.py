"""
Serializers for student-related models.
"""
from rest_framework import serializers
from django.db.models import Avg, Count
from .models import (
    StudentProfile, Subject, Class, Enrollment, Assignment, 
    Grade, Attendance, BehaviorRecord, ExtracurricularActivity, ActivityParticipation
)
from accounts.serializers import UserProfileSerializer


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for student profile information.
    """
    user = UserProfileSerializer(read_only=True)
    current_gpa = serializers.SerializerMethodField()
    total_credits = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'student_id', 'grade_level', 'gender', 'ethnicity',
            'parental_education_level', 'family_income_bracket', 'enrollment_date',
            'expected_graduation_date', 'gpa', 'current_gpa', 'total_credits',
            'has_learning_disability', 'receives_free_lunch', 'transportation_method',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_gpa', 'total_credits']
    
    def get_current_gpa(self, obj):
        """Calculate current GPA based on recent grades."""
        recent_grades = Grade.objects.filter(student=obj).select_related('assignment')
        if not recent_grades.exists():
            return None
        
        total_points = 0
        total_credits = 0
        
        for grade in recent_grades:
            percentage = grade.percentage
            # Convert percentage to GPA scale (4.0)
            if percentage >= 97:
                grade_points = 4.0
            elif percentage >= 93:
                grade_points = 3.7
            elif percentage >= 90:
                grade_points = 3.3
            elif percentage >= 87:
                grade_points = 3.0
            elif percentage >= 83:
                grade_points = 2.7
            elif percentage >= 80:
                grade_points = 2.3
            elif percentage >= 77:
                grade_points = 2.0
            elif percentage >= 73:
                grade_points = 1.7
            elif percentage >= 70:
                grade_points = 1.3
            elif percentage >= 67:
                grade_points = 1.0
            elif percentage >= 65:
                grade_points = 0.7
            else:
                grade_points = 0.0
            
            credits = grade.assignment.class_instance.subject.credit_hours
            total_points += grade_points * credits
            total_credits += credits
        
        return round(total_points / total_credits, 2) if total_credits > 0 else None
    
    def get_total_credits(self, obj):
        """Calculate total credits earned."""
        completed_enrollments = obj.enrollments.filter(status=Enrollment.Status.COMPLETED)
        return sum(enrollment.class_instance.subject.credit_hours for enrollment in completed_enrollments)


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer for subject information.
    """
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'description', 'credit_hours', 'department']


class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer for class information.
    """
    subject = SubjectSerializer(read_only=True)
    teacher = UserProfileSerializer(read_only=True)
    enrollment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'subject', 'teacher', 'term', 'year', 'section', 
            'max_students', 'enrollment_count'
        ]
    
    def get_enrollment_count(self, obj):
        """Get current enrollment count."""
        return obj.enrollments.filter(status=Enrollment.Status.ENROLLED).count()


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for enrollment information.
    """
    student = StudentProfileSerializer(read_only=True)
    class_instance = ClassSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'class_instance', 'enrollment_date', 'status', 'final_grade']


class AssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for assignment information.
    """
    class_instance = ClassSerializer(read_only=True)
    average_score = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'class_instance', 'title', 'description', 'assignment_type',
            'max_points', 'due_date', 'created_at', 'average_score', 'submission_count'
        ]
    
    def get_average_score(self, obj):
        """Calculate average score for this assignment."""
        avg = obj.grades.aggregate(avg_score=Avg('points_earned'))['avg_score']
        return round(avg, 2) if avg else None
    
    def get_submission_count(self, obj):
        """Get number of submissions."""
        return obj.grades.count()


class GradeSerializer(serializers.ModelSerializer):
    """
    Serializer for grade information.
    """
    student = StudentProfileSerializer(read_only=True)
    assignment = AssignmentSerializer(read_only=True)
    percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'assignment', 'points_earned', 'percentage',
            'submitted_at', 'graded_at', 'feedback'
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for attendance records.
    """
    student = StudentProfileSerializer(read_only=True)
    class_instance = ClassSerializer(read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'class_instance', 'date', 'status', 
            'notes', 'recorded_at'
        ]


class BehaviorRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for behavior records.
    """
    student = StudentProfileSerializer(read_only=True)
    reporter = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = BehaviorRecord
        fields = [
            'id', 'student', 'reporter', 'incident_date', 'behavior_type',
            'severity', 'description', 'action_taken', 'created_at'
        ]


class ExtracurricularActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for extracurricular activities.
    """
    advisor = UserProfileSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExtracurricularActivity
        fields = ['id', 'name', 'category', 'description', 'advisor', 'participant_count']
    
    def get_participant_count(self, obj):
        """Get current participant count."""
        return obj.participations.filter(end_date__isnull=True).count()


class ActivityParticipationSerializer(serializers.ModelSerializer):
    """
    Serializer for activity participation.
    """
    student = StudentProfileSerializer(read_only=True)
    activity = ExtracurricularActivitySerializer(read_only=True)
    
    class Meta:
        model = ActivityParticipation
        fields = [
            'id', 'student', 'activity', 'role', 'start_date', 
            'end_date', 'hours_per_week'
        ]


class StudentDashboardSerializer(serializers.Serializer):
    """
    Serializer for student dashboard data.
    """
    profile = StudentProfileSerializer()
    current_enrollments = EnrollmentSerializer(many=True)
    recent_grades = GradeSerializer(many=True)
    upcoming_assignments = AssignmentSerializer(many=True)
    attendance_summary = serializers.DictField()
    activity_participations = ActivityParticipationSerializer(many=True)


class TeacherDashboardSerializer(serializers.Serializer):
    """
    Serializer for teacher dashboard data.
    """
    profile = UserProfileSerializer()
    current_classes = ClassSerializer(many=True)
    recent_assignments = AssignmentSerializer(many=True)
    pending_grades = serializers.IntegerField()
    student_count = serializers.IntegerField()