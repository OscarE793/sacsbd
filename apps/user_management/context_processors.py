"""
Context processors para el sistema de gestión de usuarios.
"""
from django.conf import settings


def user_permissions(request):
    """
    Agrega los permisos del usuario al contexto de todos los templates.
    """
    if request.user.is_authenticated:
        # Importar aquí para evitar problemas de importación circular
        from .utils import get_user_permissions_summary, get_user_roles
        
        return {
            'user_permissions': get_user_permissions_summary(request.user),
            'user_roles': get_user_roles(request.user),
            'user_full_name': request.user.get_full_name() or request.user.username,
        }
    
    return {
        'user_permissions': {},
        'user_roles': [],
        'user_full_name': '',
    }


def system_info(request):
    """
    Agrega información del sistema al contexto.
    """
    return {
        'SYSTEM_NAME': getattr(settings, 'SYSTEM_NAME', 'SACSBD'),
        'SYSTEM_VERSION': getattr(settings, 'SYSTEM_VERSION', '1.0.0'),
        'SESSION_TIMEOUT': getattr(settings, 'SESSION_TIMEOUT', 1800),
    }