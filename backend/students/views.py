"""
Views for student-related functionality.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta
from accounts.permissions import IsStudent, IsTeacher, IsAdministrator, IsTeacherOrAdmin
from accounts.utils import get_client_ip, create_audit_log
from accounts.models import AuditLog
from .models import (
    StudentProfile, Subject, Class, Enrollment, Assignment, 
    Grade, Attendance, BehaviorRecord, ExtracurricularActivity, ActivityParticipation
)
from .serializers import (
    StudentProfileSerializer, SubjectSerializer, ClassSerializer, EnrollmentSerializer,
    AssignmentSerializer, GradeSerializer, AttendanceSerializer, BehaviorRecordSerializer,
    ExtracurricularActivitySerializer, ActivityParticipationSerializer,
    StudentDashboardSerializer, TeacherDashboardSerializer
)


class StudentProfileViewSet(ModelViewSet):
    """
    ViewSet for managing student profiles.
    """
    serializer_class = StudentProfileSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsAdministrator]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return StudentProfile.objects.all().select_related('user')
        elif user.is_teacher:
            # Teachers can see students in their classes
            return StudentProfile.objects.filter(
                enrollments__class_instance__teacher=user,
                enrollments__status=Enrollment.Status.ENROLLED
            ).distinct().select_related('user')
        elif user.is_student:
            # Students can only see their own profile
            return StudentProfile.objects.filter(user=user).select_related('user')
        
        return StudentProfile.objects.none()
    
    def perform_create(self, serializer):
        """Create student profile and log action."""
        serializer.save()
        
        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.DATA_MODIFICATION,
            description=f"Created student profile for {serializer.instance.user.email}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )


class SubjectViewSet(ModelViewSet):
    """
    ViewSet for managing subjects.
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdministrator]
        
        return [permission() for permission in permission_classes]


class ClassViewSet(ModelViewSet):
    """
    ViewSet for managing classes.
    """
    serializer_class = ClassSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdministrator]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role and query parameters."""
        user = self.request.user
        queryset = Class.objects.all().select_related('subject', 'teacher')
        
        # Filter by current term if requested
        if self.request.query_params.get('current_term'):
            current_date = timezone.now()
            current_year = current_date.year
            # Determine current term based on month
            if current_date.month >= 8:  # Fall semester
                current_term = Class.Term.FALL
            elif current_date.month >= 5:  # Summer semester
                current_term = Class.Term.SUMMER
            else:  # Spring semester
                current_term = Class.Term.SPRING
            
            queryset = queryset.filter(term=current_term, year=current_year)
        
        # Filter by teacher for teacher users
        if user.is_teacher:
            queryset = queryset.filter(teacher=user)
        
        # Filter by student enrollment for student users
        elif user.is_student:
            student_profile = getattr(user, 'student_profile', None)
            if student_profile:
                queryset = queryset.filter(
                    enrollments__student=student_profile,
                    enrollments__status=Enrollment.Status.ENROLLED
                )
        
        return queryset


class EnrollmentViewSet(ModelViewSet):
    """
    ViewSet for managing student enrollments.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_queryset(self):
        """Filter enrollments based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return Enrollment.objects.all().select_related('student__user', 'class_instance__subject', 'class_instance__teacher')
        elif user.is_teacher:
            return Enrollment.objects.filter(
                class_instance__teacher=user
            ).select_related('student__user', 'class_instance__subject')
        elif user.is_student:
            student_profile = getattr(user, 'student_profile', None)
            if student_profile:
                return Enrollment.objects.filter(
                    student=student_profile
                ).select_related('class_instance__subject', 'class_instance__teacher')
        
        return Enrollment.objects.none()


class AssignmentViewSet(ModelViewSet):
    """
    ViewSet for managing assignments.
    """
    serializer_class = AssignmentSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter assignments based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return Assignment.objects.all().select_related('class_instance__subject', 'class_instance__teacher')
        elif user.is_teacher:
            return Assignment.objects.filter(
                class_instance__teacher=user
            ).select_related('class_instance__subject')
        elif user.is_student:
            student_profile = getattr(user, 'student_profile', None)
            if student_profile:
                return Assignment.objects.filter(
                    class_instance__enrollments__student=student_profile,
                    class_instance__enrollments__status=Enrollment.Status.ENROLLED
                ).select_related('class_instance__subject', 'class_instance__teacher')
        
        return Assignment.objects.none()


class GradeViewSet(ModelViewSet):
    """
    ViewSet for managing grades.
    """
    serializer_class = GradeSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter grades based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return Grade.objects.all().select_related('student__user', 'assignment__class_instance__subject')
        elif user.is_teacher:
            return Grade.objects.filter(
                assignment__class_instance__teacher=user
            ).select_related('student__user', 'assignment__class_instance__subject')
        elif user.is_student:
            student_profile = getattr(user, 'student_profile', None)
            if student_profile:
                return Grade.objects.filter(
                    student=student_profile
                ).select_related('assignment__class_instance__subject', 'assignment__class_instance__teacher')
        
        return Grade.objects.none()


class AttendanceViewSet(ModelViewSet):
    """
    ViewSet for managing attendance records.
    """
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    
    def get_queryset(self):
        """Filter attendance based on user role."""
        user = self.request.user
        
        if user.is_administrator:
            return Attendance.objects.all().select_related('student__user', 'class_instance__subject')
        elif user.is_teacher:
            return Attendance.objects.filter(
                class_instance__teacher=user
            ).select_related('student__user', 'class_instance__subject')
        
        return Attendance.objects.none()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def student_dashboard(request):
    """
    Get comprehensive dashboard data for students.
    """
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return Response({
            'error': 'Student profile not found.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get current enrollments
    current_enrollments = Enrollment.objects.filter(
        student=student_profile,
        status=Enrollment.Status.ENROLLED
    ).select_related('class_instance__subject', 'class_instance__teacher')
    
    # Get recent grades (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_grades = Grade.objects.filter(
        student=student_profile,
        graded_at__gte=thirty_days_ago
    ).select_related('assignment__class_instance__subject').order_by('-graded_at')[:10]
    
    # Get upcoming assignments (next 14 days)
    two_weeks_from_now = timezone.now() + timedelta(days=14)
    upcoming_assignments = Assignment.objects.filter(
        class_instance__enrollments__student=student_profile,
        class_instance__enrollments__status=Enrollment.Status.ENROLLED,
        due_date__gte=timezone.now(),
        due_date__lte=two_weeks_from_now
    ).select_related('class_instance__subject').order_by('due_date')[:10]
    
    # Calculate attendance summary
    total_attendance = Attendance.objects.filter(student=student_profile).count()
    present_count = Attendance.objects.filter(
        student=student_profile,
        status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
    ).count()
    
    attendance_summary = {
        'total_days': total_attendance,
        'present_days': present_count,
        'absent_days': total_attendance - present_count,
        'attendance_rate': round((present_count / total_attendance * 100), 2) if total_attendance > 0 else 0
    }
    
    # Get activity participations
    activity_participations = ActivityParticipation.objects.filter(
        student=student_profile,
        end_date__isnull=True
    ).select_related('activity')
    
    dashboard_data = {
        'profile': StudentProfileSerializer(student_profile).data,
        'current_enrollments': EnrollmentSerializer(current_enrollments, many=True).data,
        'recent_grades': GradeSerializer(recent_grades, many=True).data,
        'upcoming_assignments': AssignmentSerializer(upcoming_assignments, many=True).data,
        'attendance_summary': attendance_summary,
        'activity_participations': ActivityParticipationSerializer(activity_participations, many=True).data
    }
    
    # Create audit log
    create_audit_log(
        user=request.user,
        action=AuditLog.Action.DATA_ACCESS,
        description="Accessed student dashboard",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response(dashboard_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsTeacher])
def teacher_dashboard(request):
    """
    Get comprehensive dashboard data for teachers.
    """
    # Get current classes
    current_date = timezone.now()
    current_year = current_date.year
    # Determine current term
    if current_date.month >= 8:
        current_term = Class.Term.FALL
    elif current_date.month >= 5:
        current_term = Class.Term.SUMMER
    else:
        current_term = Class.Term.SPRING
    
    current_classes = Class.objects.filter(
        teacher=request.user,
        term=current_term,
        year=current_year
    ).select_related('subject')
    
    # Get recent assignments
    recent_assignments = Assignment.objects.filter(
        class_instance__teacher=request.user,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).select_related('class_instance__subject').order_by('-created_at')[:10]
    
    # Count pending grades (assignments without grades)
    pending_grades = Assignment.objects.filter(
        class_instance__teacher=request.user,
        due_date__lt=timezone.now()
    ).annotate(
        grade_count=Count('grades')
    ).filter(
        grade_count__lt=Count('class_instance__enrollments', filter=Q(class_instance__enrollments__status=Enrollment.Status.ENROLLED))
    ).count()
    
    # Count total students
    student_count = StudentProfile.objects.filter(
        enrollments__class_instance__teacher=request.user,
        enrollments__status=Enrollment.Status.ENROLLED
    ).distinct().count()
    
    dashboard_data = {
        'profile': request.user,
        'current_classes': current_classes,
        'recent_assignments': recent_assignments,
        'pending_grades': pending_grades,
        'student_count': student_count
    }
    
    serializer = TeacherDashboardSerializer(dashboard_data)
    
    # Create audit log
    create_audit_log(
        user=request.user,
        action=AuditLog.Action.DATA_ACCESS,
        description="Accessed teacher dashboard",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsTeacherOrAdmin])
def class_analytics(request, class_id):
    """
    Get analytics data for a specific class.
    """
    try:
        class_instance = Class.objects.get(id=class_id)
        
        # Check permissions
        if request.user.is_teacher and class_instance.teacher != request.user:
            return Response({
                'error': 'You do not have permission to view this class.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get enrollment statistics
        enrollments = Enrollment.objects.filter(class_instance=class_instance)
        enrollment_stats = {
            'total_enrolled': enrollments.filter(status=Enrollment.Status.ENROLLED).count(),
            'total_dropped': enrollments.filter(status=Enrollment.Status.DROPPED).count(),
            'total_completed': enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
        }
        
        # Get grade statistics
        grades = Grade.objects.filter(assignment__class_instance=class_instance)
        if grades.exists():
            grade_stats = {
                'average_score': grades.aggregate(avg=Avg('points_earned'))['avg'],
                'total_assignments': Assignment.objects.filter(class_instance=class_instance).count(),
                'graded_assignments': grades.values('assignment').distinct().count(),
            }
        else:
            grade_stats = {
                'average_score': None,
                'total_assignments': Assignment.objects.filter(class_instance=class_instance).count(),
                'graded_assignments': 0,
            }
        
        # Get attendance statistics
        attendance_records = Attendance.objects.filter(class_instance=class_instance)
        if attendance_records.exists():
            total_records = attendance_records.count()
            present_records = attendance_records.filter(
                status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
            ).count()
            
            attendance_stats = {
                'total_records': total_records,
                'present_records': present_records,
                'attendance_rate': round((present_records / total_records * 100), 2) if total_records > 0 else 0
            }
        else:
            attendance_stats = {
                'total_records': 0,
                'present_records': 0,
                'attendance_rate': 0
            }
        
        analytics_data = {
            'class_info': ClassSerializer(class_instance).data,
            'enrollment_stats': enrollment_stats,
            'grade_stats': grade_stats,
            'attendance_stats': attendance_stats,
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
        
    except Class.DoesNotExist:
        return Response({
            'error': 'Class not found.'
        }, status=status.HTTP_404_NOT_FOUND)