"""
Signals para el sistema de gestión de usuarios.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Registra cuando un usuario inicia sesión exitosamente.
    """
    try:
        # Resetear intentos fallidos
        if hasattr(user, 'profile'):
            user.profile.reset_failed_attempts()
        
        # Registrar en el log de auditoría
        from .utils import log_user_action
        log_user_action(
            user,
            'login',
            f'Inicio de sesión exitoso',
            request
        )
        
        # Actualizar última actividad en la sesión
        request.session['last_activity'] = timezone.now().isoformat()
        
    except Exception as e:
        logger.error(f"Error al registrar login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Registra cuando un usuario cierra sesión.
    """
    try:
        if user:
            from .utils import log_user_action
            log_user_action(
                user,
                'logout',
                'Cierre de sesión',
                request
            )
    except Exception as e:
        logger.error(f"Error al registrar logout: {e}")


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    """
    Registra intentos de login fallidos.
    """
    try:
        from django.contrib.auth.models import User
        
        username = credentials.get('username', '')
        
        # Intentar obtener el usuario
        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        
        # Registrar el intento fallido
        from .utils import log_user_action
        log_user_action(
            user,
            'failed_login',
            f'Intento de login fallido para: {username}',
            request
        )
        
        # Si el usuario existe, incrementar intentos fallidos
        if user and hasattr(user, 'profile'):
            user.profile.increment_failed_attempts()
            
            if user.profile.is_blocked():
                # Enviar mensaje adicional sobre el bloqueo
                from django.contrib import messages
                messages.error(
                    request,
                    f'La cuenta ha sido bloqueada temporalmente debido a múltiples intentos fallidos. '
                    f'Intenta nuevamente en 30 minutos.'
                )
        
    except Exception as e:
        logger.error(f"Error al registrar login fallido: {e}")