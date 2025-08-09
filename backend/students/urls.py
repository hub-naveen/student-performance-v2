"""
URL patterns for the students app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'profiles', views.StudentProfileViewSet, basename='student-profile')
router.register(r'subjects', views.SubjectViewSet)
router.register(r'classes', views.ClassViewSet, basename='class')
router.register(r'enrollments', views.EnrollmentViewSet, basename='enrollment')
router.register(r'assignments', views.AssignmentViewSet, basename='assignment')
router.register(r'grades', views.GradeViewSet, basename='grade')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/student/', views.student_dashboard, name='student-dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher-dashboard'),
    
    # Analytics endpoints
    path('classes/<uuid:class_id>/analytics/', views.class_analytics, name='class-analytics'),
]