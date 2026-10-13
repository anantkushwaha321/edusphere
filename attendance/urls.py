from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_dashboard_view, name='attendance_dashboard'),
    path('take/', views.take_attendance_view, name='take_attendance'),
    path('sessions/<int:pk>/', views.attendance_session_detail_view, name='attendance_session_detail'),
]
