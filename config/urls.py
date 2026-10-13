from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),

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
