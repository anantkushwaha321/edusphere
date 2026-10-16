import logging
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connection

from accounts.models import StudentProfile, TeacherProfile
from academics.models import Course, Department
from announcements.models import Announcement

logger = logging.getLogger(__name__)

def home_landing_view(request):
    if request.user.is_authenticated and not request.GET.get('explore'):
        return redirect('dashboard')
    
    try:
        total_students = StudentProfile.objects.count()
        total_teachers = TeacherProfile.objects.count()
        total_courses = Course.objects.filter(is_active=True).count()
        total_departments = Department.objects.count()
        recent_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:4]
    except Exception as e:
        logger.error("Database query failed in home_landing_view: %s", e, exc_info=True)
        total_students = None
        total_teachers = None
        total_courses = None
        total_departments = None
        recent_announcements = []

    return render(request, 'pages/home.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_departments': total_departments,
        'recent_announcements': recent_announcements,
        'is_full_width_page': True,
    })


def health_check_view(request):
    """Health check endpoint for Render health checks and uptime monitoring."""
    db_ok = False
    tables = []
    migration_output = ""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        tables = connection.introspection.table_names()
        if 'accounts_user' not in tables:
            from io import StringIO
            from django.core.management import call_command
            out = StringIO()
            call_command('migrate', interactive=False, stdout=out)
            migration_output = out.getvalue()
            tables = connection.introspection.table_names()
        db_ok = True
    except Exception as e:
        logger.warning("Health check database probe failed: %s", e)
        migration_output = str(e)
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse({
        'status': 'healthy' if db_ok else 'unhealthy',
        'database': 'connected' if db_ok else 'disconnected',
        'tables_count': len(tables),
        'tables': tables,
        'migration_log': migration_output,
        'has_auth_tables': 'accounts_user' in tables,
        'has_otp_table': 'accounts_emailotpchallenge' in tables,
    }, status=status_code)



urlpatterns = [
    path('healthz/', health_check_view, name='health_check'),
    path('admin/', admin.site.urls),
    path('', home_landing_view, name='home'),

    # EduSphere Subsystems
    path('', include('accounts.urls')),
    path('academics/', include('academics.urls')),
    path('assignments/', include('assignments.urls')),
    path('attendance/', include('attendance.urls')),
    path('materials/', include('materials.urls')),
    path('announcements/', include('announcements.urls')),
    path('activity-logs/', include('activity_logs.urls')),
    path('', include('analytics.urls')),
    path('', include('compliance.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
