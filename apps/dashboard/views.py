from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse

@login_required
def dashboard_index(request):
    """Vista principal del dashboard con métricas SACSBD"""
    
    # Datos de ejemplo para el dashboard (reemplazar con datos reales)
    context = {
        'page_title': 'Dashboard Principal',
        'total_users': User.objects.filter(is_active=True).count(),
        'active_sessions': 23,  # Implementar lógica real
        'total_backups': 45,    # Implementar lógica real
        'server_status': 'online',
        'recent_activities': [
            {
                'user': 'Admin',
                'action': 'Backup completado exitosamente',
                'time': '2 minutos',
                'icon': 'ki-check-circle',
                'color': 'success'
            },
            {
                'user': 'Sistema',
                'action': 'Monitoreo de servidor iniciado',
                'time': '5 minutos', 
                'icon': 'ki-security-check',
                'color': 'primary'
            },
            {
                'user': 'Usuario01',
                'action': 'Nuevo usuario registrado',
                'time': '15 minutos',
                'icon': 'ki-add-user',
                'color': 'info'
            },
            {
                'user': 'Sistema',
                'action': 'Mantenimiento programado',
                'time': '1 hora',
                'icon': 'ki-setting-3',
                'color': 'warning'
            }
        ]
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
def dashboard_analytics(request):
    """Vista de analytics avanzados"""
    context = {
        'page_title': 'Analytics',
        'page_description': 'Análisis detallado de backups y servidores',
    }
    return render(request, 'dashboard/analytics.html', context)

@login_required
def user_profile(request):
    """Vista del perfil de usuario"""
    context = {
        'page_title': 'Mi Perfil',
        'user': request.user,
    }
    return render(request, 'dashboard/profile.html', context)

@login_required
def settings_view(request):
    """Vista de configuraciones del sistema"""
    context = {
        'page_title': 'Configuración',
    }
    return render(request, 'dashboard/settings.html', context)

def login_view(request):
    """Vista de login personalizada con Metronic"""
    
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard:index')
                messages.success(request, f'¡Bienvenido {user.get_full_name() or user.username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Credenciales inválidas. Por favor verifica tu usuario y contraseña.')
        else:
            messages.error(request, 'Por favor ingresa usuario y contraseña.')
    
    return render(request, 'auth/login.html')

@login_required
def logout_view(request):
    """Vista de logout"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'Sesión cerrada exitosamente. ¡Hasta luego {user_name}!')
    return redirect('auth:login')

@login_required
def dashboard_api_metrics(request):
    """API para obtener métricas en tiempo real"""
    
    # Datos de ejemplo (implementar lógica real)
    metrics = {
        'cpu_usage': 45,
        'memory_usage': 67,
        'disk_usage': 23,
        'network_status': 'stable',
        'active_connections': 156,
        'backup_queue': 3,
        'last_backup': '2025-06-26 23:45:00',
        'server_uptime': '15 días, 4 horas'
    }
    
    return JsonResponse(metrics)
