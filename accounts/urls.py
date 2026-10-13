from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Web UI Views
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/', views.user_detail_view, name='user_detail'),
    path('users/<int:pk>/toggle-status/', views.user_toggle_status_view, name='user_toggle_status'),

    # Professional OTP-Based Authentication REST APIs
    path('api/auth/send-otp/', api_views.api_send_otp, name='api_send_otp'),
    path('api/auth/verify-otp/', api_views.api_verify_otp, name='api_verify_otp'),
    path('api/auth/resend-otp/', api_views.api_resend_otp, name='api_resend_otp'),
    path('api/auth/logout/', api_views.api_logout, name='api_logout'),
    path('api/auth/me/', api_views.api_me, name='api_me'),
]
