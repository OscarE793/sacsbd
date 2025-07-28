# apps/user_management/urls.py
from django.urls import path
from . import views

app_name = 'user_management'

urlpatterns = [
    # Gestión de usuarios
    path('', views.user_list, name='list'),
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/crear/', views.user_create, name='create'),
    path('usuarios/<int:pk>/', views.user_detail, name='detail'),
    path('usuarios/<int:pk>/editar/', views.user_edit, name='edit'),
    path('usuarios/<int:pk>/eliminar/', views.user_delete, name='delete'),
    path('usuarios/<int:pk>/toggle-status/', views.toggle_user_status, name='toggle_status'),
    path('usuarios/<int:pk>/reset-attempts/', views.reset_failed_attempts, name='reset_attempts'),
    
    # Gestión de contraseñas
    path('usuarios/<int:pk>/cambiar-password/', views.change_password, name='change_password'),
    path('cambiar-password/', views.change_password, name='change_my_password'),
    
    # Gestión de roles
    path('roles/', views.roles_list, name='roles_list'),
    path('roles/crear/', views.role_create, name='role_create'),
    
    # Auditoría
    path('auditoria/', views.audit_logs, name='audit_logs'),
    
    # Compatibilidad con URLs antiguas
    path('create/', views.user_create, name='create_old'),
    path('<int:pk>/', views.user_detail, name='detail_old'),
    path('<int:pk>/edit/', views.user_edit, name='edit_old'),
    path('<int:pk>/delete/', views.user_delete, name='delete_old'),
]
