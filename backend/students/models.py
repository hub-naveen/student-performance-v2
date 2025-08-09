"""
Student-related models for academic performance tracking.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User
import uuid


class StudentProfile(models.Model):
    """
    Extended profile information for students.
    """
    
    class GradeLevel(models.TextChoices):
        GRADE_9 = '9', '9th Grade'
        GRADE_10 = '10', '10th Grade'
        GRADE_11 = '11', '11th Grade'
        GRADE_12 = '12', '12th Grade'
    
    class ParentalEducation(models.TextChoices):
        NONE = 'none', 'None'
        PRIMARY = 'primary', 'Primary School'
        SECONDARY = 'secondary', 'Secondary School'
        SOME_COLLEGE = 'some_college', 'Some College'
        BACHELORS = 'bachelors', "Bachelor's Degree"
        MASTERS = 'masters', "Master's Degree"
        DOCTORATE = 'doctorate', 'Doctorate'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    grade_level = models.CharField(max_length=2, choices=GradeLevel.choices)
    
    # Demographic information
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    ethnicity = models.CharField(max_length=50, blank=True)
    
    # Family background
    parental_education_level = models.CharField(max_length=20, choices=ParentalEducation.choices)
    family_income_bracket = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low (< $30,000)'),
            ('middle', 'Middle ($30,000 - $75,000)'),
            ('high', 'High (> $75,000)')
        ]
    )
    
    # Academic information
    enrollment_date = models.DateField()
    expected_graduation_date = models.DateField()
    gpa = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0.0), MaxValueValidator(4.0)], null=True, blank=True)
    
    # Additional factors
    has_learning_disability = models.BooleanField(default=False)
    receives_free_lunch = models.BooleanField(default=False)
    transportation_method = models.CharField(
        max_length=20,
        choices=[
            ('bus', 'School Bus'),
            ('car', 'Car/Carpool'),
            ('walk', 'Walking'),
            ('bike', 'Bicycle'),
            ('public', 'Public Transportation')
        ]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_profiles'
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['grade_level']),
            models.Index(fields=['gpa']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"


class Subject(models.Model):
    """
    Academic subjects/courses.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    credit_hours = models.PositiveIntegerField(default=3)
    department = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'subjects'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['department']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Class(models.Model):
    """
    Class instances for specific subjects and terms.
    """
    
    class Term(models.TextChoices):
        FALL = 'fall', 'Fall'
        SPRING = 'spring', 'Spring'
        SUMMER = 'summer', 'Summer'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='classes')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_classes')
    term = models.CharField(max_length=10, choices=Term.choices)
    year = models.PositiveIntegerField()
    section = models.CharField(max_length=10)
    max_students = models.PositiveIntegerField(default=30)
    
    class Meta:
        db_table = 'classes'
        unique_together = ['subject', 'teacher', 'term', 'year', 'section']
        indexes = [
            models.Index(fields=['term', 'year']),
            models.Index(fields=['teacher']),
        ]
    
    def __str__(self):
        return f"{self.subject.code} - {self.term} {self.year} - Section {self.section}"


class Enrollment(models.Model):
    """
    Student enrollment in classes.
    """
    
    class Status(models.TextChoices):
        ENROLLED = 'enrolled', 'Enrolled'
        DROPPED = 'dropped', 'Dropped'
        COMPLETED = 'completed', 'Completed'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)
    final_grade = models.CharField(max_length=2, blank=True)
    
    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'class_instance']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['class_instance']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.class_instance}"


class Assignment(models.Model):
    """
    Assignments for classes.
    """
    
    class Type(models.TextChoices):
        HOMEWORK = 'homework', 'Homework'
        QUIZ = 'quiz', 'Quiz'
        EXAM = 'exam', 'Exam'
        PROJECT = 'project', 'Project'
        PARTICIPATION = 'participation', 'Participation'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignment_type = models.CharField(max_length=20, choices=Type.choices)
    max_points = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assignments'
        indexes = [
            models.Index(fields=['class_instance', 'due_date']),
            models.Index(fields=['assignment_type']),
        ]
    
    def __str__(self):
        return f"{self.class_instance.subject.code} - {self.title}"


class Grade(models.Model):
    """
    Student grades for assignments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='grades')
    points_earned = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        db_table = 'grades'
        unique_together = ['student', 'assignment']
        indexes = [
            models.Index(fields=['student', 'graded_at']),
            models.Index(fields=['assignment']),
        ]
    
    @property
    def percentage(self):
        """Calculate percentage score."""
        if self.assignment.max_points > 0:
            return (self.points_earned / self.assignment.max_points) * 100
        return 0
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}: {self.points_earned}/{self.assignment.max_points}"


class Attendance(models.Model):
    """
    Student attendance records.
    """
    
    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'
        EXCUSED = 'excused', 'Excused'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['student', 'class_instance', 'date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['class_instance', 'date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.class_instance} - {self.date}: {self.status}"


class BehaviorRecord(models.Model):
    """
    Student behavior and disciplinary records.
    """
    
    class Type(models.TextChoices):
        POSITIVE = 'positive', 'Positive'
        NEGATIVE = 'negative', 'Negative'
        NEUTRAL = 'neutral', 'Neutral'
    
    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='behavior_records')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_behaviors')
    incident_date = models.DateTimeField()
    behavior_type = models.CharField(max_length=10, choices=Type.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    description = models.TextField()
    action_taken = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'behavior_records'
        indexes = [
            models.Index(fields=['student', 'incident_date']),
            models.Index(fields=['behavior_type', 'severity']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.behavior_type} - {self.incident_date.date()}"


class ExtracurricularActivity(models.Model):
    """
    Extracurricular activities and student participation.
    """
    
    class Category(models.TextChoices):
        SPORTS = 'sports', 'Sports'
        ACADEMIC = 'academic', 'Academic'
        ARTS = 'arts', 'Arts'
        COMMUNITY = 'community', 'Community Service'
        LEADERSHIP = 'leadership', 'Leadership'
        OTHER = 'other', 'Other'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField(blank=True)
    advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='advised_activities')
    
    class Meta:
        db_table = 'extracurricular_activities'
        indexes = [
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name


class ActivityParticipation(models.Model):
    """
    Student participation in extracurricular activities.
    """
    
    class Role(models.TextChoices):
        MEMBER = 'member', 'Member'
        OFFICER = 'officer', 'Officer'
        CAPTAIN = 'captain', 'Captain'
        PRESIDENT = 'president', 'President'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='activity_participations')
    activity = models.ForeignKey(ExtracurricularActivity, on_delete=models.CASCADE, related_name='participations')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    hours_per_week = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'activity_participations'
        unique_together = ['student', 'activity']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['activity']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.activity.name} ({self.role})"