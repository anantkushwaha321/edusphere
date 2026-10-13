from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list_view, name='assignment_list'),
    path('create/', views.assignment_create_view, name='assignment_create'),
    path('<int:pk>/', views.assignment_detail_view, name='assignment_detail'),
    path('<int:pk>/edit/', views.assignment_edit_view, name='assignment_edit'),
    path('<int:assignment_pk>/submit/', views.submission_submit_view, name='submission_submit'),
    path('submissions/<int:submission_pk>/grade/', views.submission_grade_view, name='submission_grade'),
]
