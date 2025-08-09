"""
WSGI config for student_performance project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_performance.settings')

application = get_wsgi_application()