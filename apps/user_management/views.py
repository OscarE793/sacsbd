from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
import logging

from .models import UserProfile, Role, UserRole, AuditLog
from .forms import (
    UserCreateForm, UserEditForm, PasswordChangeForm, 
    RoleForm, UserFilterForm
)
from .utils import log_user_action, has_permission, get_client_ip

logger = logging.getLogger(__name__)


@login_required
def user_list(request):
    """Lista de usuarios con filtros y paginación"""
    try:
        # Verificar permisos
        if not has_permission(request.user, 'puede_gestionar_usuarios'):
            return HttpResponseForbidden("No tienes permisos para ver usuarios")
        
        # Formulario de filtros
        filter_form = UserFilterForm(request.GET)
        
        # Query base
        users = User.objects.select_related('profile').prefetch_related('userrole_set__role')
        
        # Aplicar filtros
        if filter_form.is_valid():
            search = filter_form.cleaned_data.get('search')
            role = filter_form.cleaned_data.get('role')
            is_active = filter_form.cleaned_data.get('is_active')
            is_staff = filter_form.cleaned_data.get('is_staff')
            
            if search:
                users = users.filter(
                    Q(username__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search)
                )
            
            if role:
                users = users.filter(
                    userrole__role=role,
                    userrole__activo=True
                )
            
            if is_active:
                users = users.filter(is_active=is_active.lower() == 'true')
            
            if is_staff:
                users = users.filter(is_staff=is_staff.lower() == 'true')
        
        # Ordenar
        users = users.order_by('-date_joined')
        
        # Paginación
        paginator = Paginator(users, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Estadísticas
        stats = {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'staff': User.objects.filter(is_staff=True).count(),
            'with_roles': User.objects.filter(userrole__activo=True).distinct().count(),
        }
        
        # Log de acción
        log_user_action(request.user, 'view_users', 'Vista de lista de usuarios', request)
        
        context = {
            'page_title': 'Gestión de Usuarios',
            'users': page_obj,
            'filter_form': filter_form,
            'stats': stats,
        }
        
        return render(request, 'user_management/list.html', context)
        
    except Exception as e:
        logger.error(f"Error en user_list: {e}")
        messages.error(request, f'Error al cargar la lista de usuarios: {str(e)}')
        return render(request, 'user_management/list.html', {'page_title': 'Gestión de Usuarios'})


@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create(request):
    """Crear nuevo usuario"""
    try:
        if request.method == 'POST':
            form = UserCreateForm(request.POST)
            if form.is_valid():
                user = form.save()
                
                # Log de acción
                log_user_action(
                    request.user, 
                    'create_user', 
                    f'Usuario creado: {user.username}',
                    request,
                    affected_user=user
                )
                
                messages.success(request, f'Usuario {user.username} creado exitosamente.')
                return redirect('user_management:detail', pk=user.pk)
            else:
                messages.error(request, 'Por favor corrige los errores del formulario.')
        else:
            form = UserCreateForm()
        
        context = {
            'page_title': 'Crear Usuario',
            'form': form,
        }
        
        return render(request, 'user_management/create.html', context)
        
    except Exception as e:
        logger.error(f"Error en user_create: {e}")
        messages.error(request, f'Error al crear usuario: {str(e)}')
        return redirect('user_management:list')


@login_required
def user_detail(request, pk):
    """Detalle de usuario"""
    try:
        user = get_object_or_404(User, pk=pk)
        
        # Verificar permisos (puede ver su propio perfil o tener permisos de gestión)
        if request.user != user and not has_permission(request.user, 'puede_gestionar_usuarios'):
            return HttpResponseForbidden("No tienes permisos para ver este usuario")
        
        # Obtener roles activos
        user_roles = UserRole.objects.filter(user=user, activo=True).select_related('role')
        
        # Obtener logs de auditoría recientes
        recent_logs = AuditLog.objects.filter(user=user).order_by('-timestamp')[:10]
        
        # Estadísticas del usuario
        user_stats = {
            'total_logins': AuditLog.objects.filter(user=user, action='login').count(),
            'failed_attempts': user.profile.intentos_fallidos if hasattr(user, 'profile') else 0,
            'is_blocked': user.profile.is_blocked() if hasattr(user, 'profile') else False,
            'roles_count': user_roles.count(),
        }
        
        context = {
            'page_title': f'Usuario: {user.username}',
            'user_detail': user,
            'user_roles': user_roles,
            'recent_logs': recent_logs,
            'user_stats': user_stats,
        }
        
        return render(request, 'user_management/detail.html', context)
        
    except Exception as e:
        logger.error(f"Error en user_detail: {e}")
        messages.error(request, f'Error al cargar el usuario: {str(e)}')
        return redirect('user_management:list')


@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_edit(request, pk):
    """Editar usuario"""
    try:
        user = get_object_or_404(User, pk=pk)
        
        if request.method == 'POST':
            form = UserEditForm(request.POST, instance=user)
            if form.is_valid():
                user = form.save()
                
                # Log de acción
                log_user_action(
                    request.user,
                    'update_user',
                    f'Usuario actualizado: {user.username}',
                    request,
                    affected_user=user
                )
                
                messages.success(request, f'Usuario {user.username} actualizado exitosamente.')
                return redirect('user_management:detail', pk=user.pk)
            else:
                messages.error(request, 'Por favor corrige los errores del formulario.')
        else:
            form = UserEditForm(instance=user)
        
        context = {
            'page_title': f'Editar Usuario: {user.username}',
            'form': form,
            'user_edit': user,
        }
        
        return render(request, 'user_management/edit.html', context)
        
    except Exception as e:
        logger.error(f"Error en user_edit: {e}")
        messages.error(request, f'Error al editar usuario: {str(e)}')
        return redirect('user_management:list')


@login_required
@require_http_methods(["POST"])
def user_delete(request, pk):
    """Eliminar/desactivar usuario"""
    try:
        user = get_object_or_404(User, pk=pk)
        
        # Verificar permisos
        if not has_permission(request.user, 'puede_gestionar_usuarios'):
            return JsonResponse({'success': False, 'message': 'Sin permisos'})
        
        # No permitir auto-eliminación
        if request.user == user:
            return JsonResponse({'success': False, 'message': 'No puedes eliminar tu propia cuenta'})
        
        # No eliminar, solo desactivar
        user.is_active = False
        user.save()
        
        # Desactivar todos los roles
        UserRole.objects.filter(user=user).update(activo=False)
        
        # Log de acción
        log_user_action(
            request.user,
            'delete_user',
            f'Usuario desactivado: {user.username}',
            request,
            affected_user=user
        )
        
        messages.success(request, f'Usuario {user.username} desactivado exitosamente.')
        return JsonResponse({'success': True, 'message': 'Usuario desactivado'})
        
    except Exception as e:
        logger.error(f"Error en user_delete: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def change_password(request, pk=None):
    """Cambiar contraseña"""
    try:
        # Si no se especifica pk, cambiar la propia contraseña
        if pk is None:
            user = request.user
        else:
            user = get_object_or_404(User, pk=pk)
            # Verificar permisos para cambiar contraseña de otro usuario
            if request.user != user and not has_permission(request.user, 'puede_gestionar_usuarios'):
                return HttpResponseForbidden("No tienes permisos para cambiar esta contraseña")
        
        if request.method == 'POST':
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                
                # Si cambió su propia contraseña, actualizar la sesión
                if request.user == user:
                    update_session_auth_hash(request, user)
                
                # Log de acción
                log_user_action(
                    request.user,
                    'change_password',
                    f'Contraseña cambiada para: {user.username}',
                    request,
                    affected_user=user
                )
                
                messages.success(request, 'Contraseña cambiada exitosamente.')
                return redirect('user_management:detail', pk=user.pk)
            else:
                messages.error(request, 'Por favor corrige los errores del formulario.')
        else:
            form = PasswordChangeForm(user)
        
        context = {
            'page_title': f'Cambiar Contraseña: {user.username}',
            'form': form,
            'user_edit': user,
        }
        
        return render(request, 'user_management/change_password.html', context)
        
    except Exception as e:
        logger.error(f"Error en change_password: {e}")
        messages.error(request, f'Error al cambiar contraseña: {str(e)}')
        return redirect('user_management:list')


@login_required
@permission_required('auth.view_user', raise_exception=True)
def roles_list(request):
    """Lista de roles"""
    try:
        roles = Role.objects.annotate(
            users_count=Count('userrole', filter=Q(userrole__activo=True))
        ).order_by('name')
        
        context = {
            'page_title': 'Gestión de Roles',
            'roles': roles,
        }
        
        return render(request, 'user_management/roles_list.html', context)
        
    except Exception as e:
        logger.error(f"Error en roles_list: {e}")
        messages.error(request, f'Error al cargar roles: {str(e)}')
        return render(request, 'user_management/roles_list.html', {'page_title': 'Gestión de Roles'})


@login_required
@permission_required('auth.add_user', raise_exception=True)
def role_create(request):
    """Crear nuevo rol"""
    try:
        if request.method == 'POST':
            form = RoleForm(request.POST)
            if form.is_valid():
                role = form.save()
                messages.success(request, f'Rol {role.name} creado exitosamente.')
                return redirect('user_management:roles_list')
            else:
                messages.error(request, 'Por favor corrige los errores del formulario.')
        else:
            form = RoleForm()
        
        context = {
            'page_title': 'Crear Rol',
            'form': form,
        }
        
        return render(request, 'user_management/role_create.html', context)
        
    except Exception as e:
        logger.error(f"Error en role_create: {e}")
        messages.error(request, f'Error al crear rol: {str(e)}')
        return redirect('user_management:roles_list')


@login_required
@permission_required('auth.view_user', raise_exception=True)
def audit_logs(request):
    """Ver logs de auditoría"""
    try:
        logs = AuditLog.objects.select_related('user', 'affected_user').order_by('-timestamp')
        
        # Filtros
        user_filter = request.GET.get('user')
        action_filter = request.GET.get('action')
        
        if user_filter:
            logs = logs.filter(user__username__icontains=user_filter)
        
        if action_filter:
            logs = logs.filter(action=action_filter)
        
        # Paginación
        paginator = Paginator(logs, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_title': 'Logs de Auditoría',
            'logs': page_obj,
            'actions': AuditLog.ACTIONS,
        }
        
        return render(request, 'user_management/audit_logs.html', context)
        
    except Exception as e:
        logger.error(f"Error en audit_logs: {e}")
        messages.error(request, f'Error al cargar logs: {str(e)}')
        return render(request, 'user_management/audit_logs.html', {'page_title': 'Logs de Auditoría'})


@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, pk):
    """Activar/desactivar usuario"""
    try:
        user = get_object_or_404(User, pk=pk)
        
        # Verificar permisos
        if not has_permission(request.user, 'puede_gestionar_usuarios'):
            return JsonResponse({'success': False, 'message': 'Sin permisos'})
        
        # No permitir auto-desactivación
        if request.user == user:
            return JsonResponse({'success': False, 'message': 'No puedes desactivar tu propia cuenta'})
        
        # Cambiar estado
        user.is_active = not user.is_active
        user.save()
        
        action = 'activado' if user.is_active else 'desactivado'
        
        # Log de acción
        log_user_action(
            request.user,
            'toggle_user_status',
            f'Usuario {action}: {user.username}',
            request,
            affected_user=user
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Usuario {action}',
            'is_active': user.is_active
        })
        
    except Exception as e:
        logger.error(f"Error en toggle_user_status: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def reset_failed_attempts(request, pk):
    """Resetear intentos fallidos de login"""
    try:
        user = get_object_or_404(User, pk=pk)
        
        # Verificar permisos
        if not has_permission(request.user, 'puede_gestionar_usuarios'):
            return JsonResponse({'success': False, 'message': 'Sin permisos'})
        
        # Resetear intentos fallidos
        if hasattr(user, 'profile'):
            user.profile.reset_failed_attempts()
        
        # Log de acción
        log_user_action(
            request.user,
            'reset_failed_attempts',
            f'Intentos fallidos reseteados para: {user.username}',
            request,
            affected_user=user
        )
        
        return JsonResponse({'success': True, 'message': 'Intentos fallidos reseteados'})
        
    except Exception as e:
        logger.error(f"Error en reset_failed_attempts: {e}")
        return JsonResponse({'success': False, 'message': str(e)})
