"""
Template tags para el sistema de gestión de usuarios.
"""
from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def has_perm(user, permission_name):
    """
    Verifica si un usuario tiene un permiso específico.
    
    Uso en template:
        {% if user|has_perm:"puede_gestionar_usuarios" %}
            ...
        {% endif %}
    """
    from apps.user_management.utils import has_permission
    return has_permission(user, permission_name)


@register.filter
def user_display_name(user):
    """
    Obtiene el nombre de display de un usuario.
    
    Uso en template:
        {{ user|user_display_name }}
    """
    if not user or not isinstance(user, User):
        return ''
    from apps.user_management.utils import format_user_display_name
    return format_user_display_name(user)


@register.simple_tag
def user_roles_list(user):
    """
    Obtiene los roles de un usuario como lista.
    
    Uso en template:
        {% user_roles_list user as roles %}
        {% for role in roles %}
            {{ role.name }}
        {% endfor %}
    """
    from apps.user_management.utils import get_user_roles
    return get_user_roles(user)


@register.inclusion_tag('user_management/tags/user_badge.html')
def user_badge(user):
    """
    Muestra un badge con información del usuario.
    
    Uso en template:
        {% user_badge user %}
    """
    from apps.user_management.utils import format_user_display_name
    return {
        'user': user,
        'display_name': format_user_display_name(user) if user else '',
        'is_online': False,  # Podría implementarse con un sistema de presencia
    }


@register.inclusion_tag('user_management/tags/permission_badges.html')
def permission_badges(user):
    """
    Muestra badges con los permisos del usuario.
    
    Uso en template:
        {% permission_badges user %}
    """
    permissions = []
    
    if user and user.is_authenticated:
        from apps.user_management.utils import has_permission
        
        if user.is_superuser:
            permissions.append({
                'name': 'Superusuario',
                'icon': 'fa-crown',
                'color': 'danger'
            })
        
        if has_permission(user, 'es_administrador'):
            permissions.append({
                'name': 'Administrador',
                'icon': 'fa-shield-alt',
                'color': 'danger'
            })
        
        if has_permission(user, 'puede_gestionar_usuarios'):
            permissions.append({
                'name': 'Gestión Usuarios',
                'icon': 'fa-users-cog',
                'color': 'primary'
            })
        
        if has_permission(user, 'puede_ver_reportes'):
            permissions.append({
                'name': 'Reportes',
                'icon': 'fa-chart-bar',
                'color': 'info'
            })
        
        if has_permission(user, 'puede_gestionar_backups'):
            permissions.append({
                'name': 'Backups',
                'icon': 'fa-database',
                'color': 'success'
            })
        
        if has_permission(user, 'puede_monitorear_servidores'):
            permissions.append({
                'name': 'Servidores',
                'icon': 'fa-server',
                'color': 'warning'
            })
    
    return {
        'permissions': permissions
    }


@register.filter
def is_user_active(user):
    """
    Verifica si un usuario está activo.
    
    Uso en template:
        {% if user|is_user_active %}
            Usuario activo
        {% endif %}
    """
    return user and user.is_active


@register.filter
def user_role_names(user):
    """
    Obtiene los nombres de los roles de un usuario como string.
    
    Uso en template:
        {{ user|user_role_names }}
    """
    if not user or not user.is_authenticated:
        return ''
    
    from apps.user_management.models import UserRole
    roles = UserRole.objects.filter(
        user=user,
        activo=True
    ).select_related('role')
    
    return ', '.join([ur.role.name for ur in roles]) or 'Sin roles'