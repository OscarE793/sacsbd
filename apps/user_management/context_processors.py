"""
Context processors para el sistema de gestión de usuarios.
"""
from django.conf import settings
from django.core.cache import cache


def user_permissions(request):
    """
    Agrega los permisos del usuario al contexto de todos los templates.
    Usa caché para evitar consultas repetitivas a la base de datos.
    """
    if request.user.is_authenticated:
        # Clave de caché única por usuario
        cache_key = f'user_perms_{request.user.id}'

        # Intentar obtener desde caché (válido por 5 minutos)
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Importar aquí para evitar problemas de importación circular
            from .utils import get_user_permissions_summary, get_user_roles

            cached_data = {
                'user_permissions': get_user_permissions_summary(request.user),
                'user_roles': list(get_user_roles(request.user).values('id', 'name', 'description')),
                'user_full_name': request.user.get_full_name() or request.user.username,
            }

            # Guardar en caché por 5 minutos (300 segundos)
            cache.set(cache_key, cached_data, 300)

        return cached_data

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