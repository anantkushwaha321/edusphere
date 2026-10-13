from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),

    path('reports/student/', views.student_report_card_view, name='my_report_card'),
    path('reports/student/<int:student_id>/', views.student_report_card_view, name='student_report_card'),
    path('gradebook/course/<int:course_id>/', views.course_gradebook_view, name='course_gradebook'),
    path('gradebook/course/<int:course_id>/export/', views.export_gradebook_csv, name='export_gradebook_csv'),
    path('attendance/course/<int:course_id>/export/', views.export_attendance_csv, name='export_attendance_csv'),
]
