from django.urls import path
from . import views

urlpatterns = [
    path('departments/', views.department_list_view, name='department_list'),
    path('departments/create/', views.department_create_view, name='department_create'),
    path('departments/<int:pk>/', views.department_detail_view, name='department_detail'),

    path('courses/', views.course_list_view, name='course_list'),
    path('courses/create/', views.course_create_view, name='course_create'),
    path('courses/<int:pk>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_edit_view, name='course_edit'),
    path('courses/<int:pk>/enroll/', views.course_enroll_view, name='course_enroll'),
    path('courses/<int:course_pk>/unenroll/<int:student_pk>/', views.course_unenroll_view, name='course_unenroll'),
]
