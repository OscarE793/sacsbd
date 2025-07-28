"""
Decoradores personalizados para el sistema de gestión de usuarios.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def require_permission(permission_name, redirect_url=None):
    """
    Decorador para verificar que el usuario tenga un permiso específico.
    
    Uso:
        @require_permission('puede_gestionar_usuarios')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('authentication:login')
            
            from .utils import has_permission
            if not has_permission(request.user, permission_name):
                if redirect_url:
                    messages.error(request, 'No tienes permisos para acceder a esta página.')
                    return redirect(redirect_url)
                else:
                    return HttpResponseForbidden(
                        f'No tienes el permiso "{permission_name}" para acceder a esta página.'
                    )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_names):
    """
    Decorador para verificar que el usuario tenga al menos uno de los permisos especificados.
    
    Uso:
        @require_any_permission('puede_gestionar_usuarios', 'es_administrador')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('authentication:login')
            
            from .utils import has_permission
            for permission_name in permission_names:
                if has_permission(request.user, permission_name):
                    return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden(
                f'No tienes ninguno de los permisos requeridos: {", ".join(permission_names)}'
            )
        return wrapper
    return decorator


def require_all_permissions(*permission_names):
    """
    Decorador para verificar que el usuario tenga todos los permisos especificados.
    
    Uso:
        @require_all_permissions('puede_ver_reportes', 'puede_gestionar_backups')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('authentication:login')
            
            from .utils import has_permission
            missing_permissions = []
            for permission_name in permission_names:
                if not has_permission(request.user, permission_name):
                    missing_permissions.append(permission_name)
            
            if missing_permissions:
                return HttpResponseForbidden(
                    f'Te faltan los siguientes permisos: {", ".join(missing_permissions)}'
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorador que requiere que el usuario sea administrador.
    
    Uso:
        @admin_required
        def mi_vista(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('authentication:login')
        
        from .utils import has_permission
        if not (request.user.is_superuser or has_permission(request.user, 'es_administrador')):
            return HttpResponseForbidden(
                'Esta página está disponible solo para administradores.'
            )
        
        return view_func(request, *args, **kwargs)
    return wrapper