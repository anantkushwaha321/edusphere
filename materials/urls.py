from django.urls import path
from . import views

urlpatterns = [
    path('', views.material_list_view, name='material_list'),
    path('upload/', views.material_upload_view, name='material_upload'),
    path('<int:pk>/download/', views.material_download_view, name='material_download'),
    path('<int:pk>/delete/', views.material_delete_view, name='material_delete'),
]
