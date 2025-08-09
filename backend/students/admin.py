"""
Admin configuration for the students app.
"""
from django.contrib import admin
from .models import (
    StudentProfile, Subject, Class, Enrollment, Assignment, 
    Grade, Attendance, BehaviorRecord, ExtracurricularActivity, ActivityParticipation
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for StudentProfile model.
    """
    list_display = ['student_id', 'user', 'grade_level', 'gpa', 'enrollment_date']
    list_filter = ['grade_level', 'gender', 'parental_education_level', 'family_income_bracket']
    search_fields = ['student_id', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'student_id', 'grade_level', 'gender', 'ethnicity')
        }),
        ('Family Background', {
            'fields': ('parental_education_level', 'family_income_bracket')
        }),
        ('Academic Information', {
            'fields': ('enrollment_date', 'expected_graduation_date', 'gpa')
        }),
        ('Additional Factors', {
            'fields': ('has_learning_disability', 'receives_free_lunch', 'transportation_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """
    Admin interface for Subject model.
    """
    list_display = ['code', 'name', 'department', 'credit_hours']
    list_filter = ['department', 'credit_hours']
    search_fields = ['code', 'name', 'department']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """
    Admin interface for Class model.
    """
    list_display = ['subject', 'teacher', 'term', 'year', 'section', 'max_students']
    list_filter = ['term', 'year', 'subject__department']
    search_fields = ['subject__code', 'subject__name', 'teacher__email']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Enrollment model.
    """
    list_display = ['student', 'class_instance', 'status', 'enrollment_date', 'final_grade']
    list_filter = ['status', 'enrollment_date', 'class_instance__term', 'class_instance__year']
    search_fields = ['student__student_id', 'student__user__email', 'class_instance__subject__code']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Assignment model.
    """
    list_display = ['title', 'class_instance', 'assignment_type', 'max_points', 'due_date']
    list_filter = ['assignment_type', 'due_date', 'class_instance__subject__department']
    search_fields = ['title', 'class_instance__subject__code']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """
    Admin interface for Grade model.
    """
    list_display = ['student', 'assignment', 'points_earned', 'percentage', 'graded_at']
    list_filter = ['graded_at', 'assignment__assignment_type']
    search_fields = ['student__student_id', 'assignment__title']
    
    def percentage(self, obj):
        return f"{obj.percentage:.1f}%"


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Admin interface for Attendance model.
    """
    list_display = ['student', 'class_instance', 'date', 'status']
    list_filter = ['status', 'date', 'class_instance__subject__department']
    search_fields = ['student__student_id', 'class_instance__subject__code']


@admin.register(BehaviorRecord)
class BehaviorRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for BehaviorRecord model.
    """
    list_display = ['student', 'behavior_type', 'severity', 'incident_date', 'reporter']
    list_filter = ['behavior_type', 'severity', 'incident_date']
    search_fields = ['student__student_id', 'description']


@admin.register(ExtracurricularActivity)
class ExtracurricularActivityAdmin(admin.ModelAdmin):
    """
    Admin interface for ExtracurricularActivity model.
    """
    list_display = ['name', 'category', 'advisor']
    list_filter = ['category']
    search_fields = ['name', 'description']


@admin.register(ActivityParticipation)
class ActivityParticipationAdmin(admin.ModelAdmin):
    """
    Admin interface for ActivityParticipation model.
    """
    list_display = ['student', 'activity', 'role', 'start_date', 'end_date']
    list_filter = ['role', 'start_date', 'activity__category']
    search_fields = ['student__student_id', 'activity__name']