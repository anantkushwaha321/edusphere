from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from accounts.models import StudentProfile, TeacherProfile
from academics.models import Course, Department
from announcements.models import Announcement

def home_landing_view(request):
    if request.user.is_authenticated and not request.GET.get('explore'):
        return redirect('dashboard')
    
    return render(request, 'pages/home.html', {
        'total_students': StudentProfile.objects.count(),
        'total_teachers': TeacherProfile.objects.count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_departments': Department.objects.count(),
        'recent_announcements': Announcement.objects.filter(is_active=True).order_by('-created_at')[:4],
        'is_full_width_page': True,
    })

urlpatterns = [
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
