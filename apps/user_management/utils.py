# apps/user_management/utils.py
from django.utils import timezone
from django.contrib.auth.models import User
from .models import AuditLog, UserRole, Role
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Obtiene el user agent del cliente"""
    return request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar longitud


def log_user_action(user, action, description, request=None, affected_user=None, metadata=None):
    """Registra una acción del usuario en el log de auditoría"""
    try:
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
        
        AuditLog.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            affected_user=affected_user,
            metadata=metadata or {}
        )
        
    except Exception as e:
        logger.error(f"Error logging user action: {e}")


def has_permission(user, permission_name):
    """
    Verifica si un usuario tiene un permiso específico basado en sus roles
    """
    if not user or not user.is_authenticated:
        return False
    
    # Los superusuarios tienen todos los permisos
    if user.is_superuser:
        return True
    
    # Verificar permisos por roles
    try:
        user_roles = UserRole.objects.filter(
            user=user,
            activo=True,
            role__activo=True
        ).select_related('role')
        
        for user_role in user_roles:
            role = user_role.role
            
            # Verificar permisos específicos del rol
            if permission_name == 'puede_gestionar_usuarios' and role.puede_gestionar_usuarios:
                return True
            elif permission_name == 'puede_ver_reportes' and role.puede_ver_reportes:
                return True
            elif permission_name == 'puede_gestionar_backups' and role.puede_gestionar_backups:
                return True
            elif permission_name == 'puede_monitorear_servidores' and role.puede_monitorear_servidores:
                return True
            elif permission_name == 'es_administrador' and role.es_administrador:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking permissions: {e}")
        return False


def get_user_roles(user):
    """Obtiene los roles activos de un usuario"""
    if not user or not user.is_authenticated:
        return Role.objects.none()
    
    try:
        return Role.objects.filter(
            userrole__user=user,
            userrole__activo=True,
            activo=True
        )
    except Exception as e:
        logger.error(f"Error getting user roles: {e}")
        return Role.objects.none()


def get_user_permissions_summary(user):
    """Obtiene un resumen de los permisos de un usuario"""
    if not user or not user.is_authenticated:
        return {}
    
    if user.is_superuser:
        return {
            'es_administrador': True,
            'puede_gestionar_usuarios': True,
            'puede_ver_reportes': True,
            'puede_gestionar_backups': True,
            'puede_monitorear_servidores': True,
        }
    
    try:
        permissions = {
            'es_administrador': False,
            'puede_gestionar_usuarios': False,
            'puede_ver_reportes': False,
            'puede_gestionar_backups': False,
            'puede_monitorear_servidores': False,
        }
        
        user_roles = UserRole.objects.filter(
            user=user,
            activo=True,
            role__activo=True
        ).select_related('role')
        
        for user_role in user_roles:
            role = user_role.role
            
            if role.es_administrador:
                permissions['es_administrador'] = True
            if role.puede_gestionar_usuarios:
                permissions['puede_gestionar_usuarios'] = True
            if role.puede_ver_reportes:
                permissions['puede_ver_reportes'] = True
            if role.puede_gestionar_backups:
                permissions['puede_gestionar_backups'] = True
            if role.puede_monitorear_servidores:
                permissions['puede_monitorear_servidores'] = True
        
        return permissions
        
    except Exception as e:
        logger.error(f"Error getting user permissions summary: {e}")
        return {}


def check_user_access_restrictions(user, request=None):
    """
    Verifica las restricciones de acceso de un usuario
    Retorna un diccionario con el estado de las verificaciones
    OPTIMIZADO: Usa caché para evitar consultas repetitivas
    """
    if not user or not user.is_authenticated:
        return {'allowed': False, 'reason': 'Usuario no autenticado'}

    # Usar caché para restricciones (válido por 5 minutos)
    from django.core.cache import cache
    cache_key = f'user_restrictions_{user.id}'
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        # Verificar IP en tiempo real (no se cachea porque puede cambiar)
        if request and cached_result.get('check_ip', False):
            try:
                profile = user.profile
                if profile.ip_permitidas:
                    client_ip = get_client_ip(request)
                    if not profile.can_access_from_ip(client_ip):
                        return {
                            'allowed': False,
                            'reason': f'Acceso no permitido desde la IP {client_ip}'
                        }
            except Exception:
                pass

        return cached_result

    try:
        profile = user.profile

        # Verificar si está bloqueado
        if profile.is_blocked():
            result = {
                'allowed': False,
                'reason': f'Usuario bloqueado hasta {profile.bloqueado_hasta}'
            }
            cache.set(cache_key, result, 60)  # Cachear por 1 minuto solo
            return result

        # Verificar IP si está configurada
        check_ip = bool(profile.ip_permitidas)
        if request and check_ip:
            client_ip = get_client_ip(request)
            if not profile.can_access_from_ip(client_ip):
                return {
                    'allowed': False,
                    'reason': f'Acceso no permitido desde la IP {client_ip}'
                }

        # Verificar horario si está configurado
        if profile.horario_acceso_inicio and profile.horario_acceso_fin:
            current_time = timezone.now().time()
            if not profile.can_access_at_time(current_time):
                return {
                    'allowed': False,
                    'reason': f'Acceso fuera del horario permitido ({profile.horario_acceso_inicio} - {profile.horario_acceso_fin})'
                }

        # Verificar si requiere cambio de contraseña
        if profile.cambio_password_requerido:
            result = {
                'allowed': True,
                'require_password_change': True,
                'reason': 'Se requiere cambio de contraseña',
                'check_ip': check_ip
            }
            cache.set(cache_key, result, 300)
            return result

        result = {'allowed': True, 'check_ip': check_ip}
        cache.set(cache_key, result, 300)  # Cachear por 5 minutos
        return result
        
    except Exception as e:
        logger.error(f"Error checking user access restrictions: {e}")
        return {'allowed': True}  # En caso de error, permitir acceso


def create_default_roles():
    """Crea los roles por defecto del sistema"""
    try:
        # Rol de Administrador
        admin_role, created = Role.objects.get_or_create(
            name='Administrador',
            defaults={
                'description': 'Administrador del sistema con todos los permisos',
                'es_administrador': True,
                'puede_gestionar_usuarios': True,
                'puede_ver_reportes': True,
                'puede_gestionar_backups': True,
                'puede_monitorear_servidores': True,
            }
        )
        
        # Rol de Operador de Reportes
        reports_role, created = Role.objects.get_or_create(
            name='Operador de Reportes',
            defaults={
                'description': 'Usuario que puede ver y generar reportes',
                'es_administrador': False,
                'puede_gestionar_usuarios': False,
                'puede_ver_reportes': True,
                'puede_gestionar_backups': False,
                'puede_monitorear_servidores': False,
            }
        )
        
        # Rol de Operador de Backups
        backup_role, created = Role.objects.get_or_create(
            name='Operador de Backups',
            defaults={
                'description': 'Usuario que puede gestionar backups',
                'es_administrador': False,
                'puede_gestionar_usuarios': False,
                'puede_ver_reportes': True,
                'puede_gestionar_backups': True,
                'puede_monitorear_servidores': False,
            }
        )
        
        # Rol de Monitor de Servidores
        monitor_role, created = Role.objects.get_or_create(
            name='Monitor de Servidores',
            defaults={
                'description': 'Usuario que puede monitorear servidores',
                'es_administrador': False,
                'puede_gestionar_usuarios': False,
                'puede_ver_reportes': True,
                'puede_gestionar_backups': False,
                'puede_monitorear_servidores': True,
            }
        )
        
        # Rol de Usuario Básico
        basic_role, created = Role.objects.get_or_create(
            name='Usuario Básico',
            defaults={
                'description': 'Usuario con permisos básicos de solo lectura',
                'es_administrador': False,
                'puede_gestionar_usuarios': False,
                'puede_ver_reportes': True,
                'puede_gestionar_backups': False,
                'puede_monitorear_servidores': False,
            }
        )
        
        logger.info("Roles por defecto creados exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error creating default roles: {e}")
        return False


def assign_role_to_user(user, role_name, assigned_by=None):
    """Asigna un rol a un usuario"""
    try:
        role = Role.objects.get(name=role_name, activo=True)
        
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={
                'asignado_por': assigned_by,
                'activo': True
            }
        )
        
        if not created and not user_role.activo:
            user_role.activo = True
            user_role.asignado_por = assigned_by
            user_role.save()
        
        return True
        
    except Role.DoesNotExist:
        logger.error(f"Role '{role_name}' does not exist")
        return False
    except Exception as e:
        logger.error(f"Error assigning role to user: {e}")
        return False


def remove_role_from_user(user, role_name):
    """Remueve un rol de un usuario"""
    try:
        UserRole.objects.filter(
            user=user,
            role__name=role_name
        ).update(activo=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Error removing role from user: {e}")
        return False


def get_users_by_role(role_name):
    """Obtiene todos los usuarios con un rol específico"""
    try:
        return User.objects.filter(
            userrole__role__name=role_name,
            userrole__activo=True,
            is_active=True
        ).distinct()
        
    except Exception as e:
        logger.error(f"Error getting users by role: {e}")
        return User.objects.none()


def validate_password_strength(password):
    """Valida la fortaleza de una contraseña"""
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not any(c.isupper() for c in password):
        errors.append("La contraseña debe contener al menos una mayúscula")
    
    if not any(c.islower() for c in password):
        errors.append("La contraseña debe contener al menos una minúscula")
    
    if not any(c.isdigit() for c in password):
        errors.append("La contraseña debe contener al menos un número")
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("La contraseña debe contener al menos un carácter especial")
    
    return len(errors) == 0, errors


def format_user_display_name(user):
    """Formatea el nombre de display de un usuario"""
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return user.username


def get_user_activity_summary(user, days=30):
    """Obtiene un resumen de actividad del usuario"""
    try:
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        logs = AuditLog.objects.filter(
            user=user,
            timestamp__gte=start_date
        )
        
        return {
            'total_actions': logs.count(),
            'logins': logs.filter(action='login').count(),
            'failed_logins': logs.filter(action='failed_login').count(),
            'last_login': logs.filter(action='login').first(),
            'last_activity': logs.first(),
        }
        
    except Exception as e:
        logger.error(f"Error getting user activity summary: {e}")
        return {}
