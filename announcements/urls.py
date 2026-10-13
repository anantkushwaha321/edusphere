from django.urls import path
from . import views

urlpatterns = [
    path('', views.announcement_list_view, name='announcement_list'),
    path('create/', views.announcement_create_view, name='announcement_create'),
    path('<int:pk>/', views.announcement_detail_view, name='announcement_detail'),

    path('notifications/', views.notification_list_view, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/read-all/', views.notification_mark_all_read_view, name='notification_mark_all_read'),
]
