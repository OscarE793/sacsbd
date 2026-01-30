"""
Middleware para el sistema de gestión de usuarios.
Incluye tracking de actividad y verificación de restricciones de acceso.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class UserTrackingMiddleware:
    """
    Middleware para rastrear la actividad de los usuarios.
    Registra accesos al sistema y verifica restricciones.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que no requieren tracking
        self.excluded_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
        ]
        
        # URLs que requieren verificación especial
        self.protected_paths = [
            '/admin/',
            '/usuarios/',
            '/backups/',
            '/servidores/',
        ]

    def __call__(self, request):
        # Verificar si la ruta debe ser excluida
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return self.get_response(request)

        # Procesar solo usuarios autenticados
        if request.user.is_authenticated:
            try:
                # Solo verificar restricciones en páginas de login o cada 5 minutos
                # Esto reduce drásticamente las consultas a la BD
                last_check = request.session.get('last_restriction_check')
                current_time = timezone.now().timestamp()

                # Verificar solo si es login o han pasado 5 minutos (300 segundos)
                should_check = (
                    last_check is None or
                    (current_time - last_check) > 300 or
                    'login' in request.path or
                    'auth' in request.path
                )

                if should_check:
                    # Importar aquí para evitar problemas de importación circular
                    from .utils import check_user_access_restrictions

                    # Verificar restricciones de acceso
                    access_check = check_user_access_restrictions(request.user, request)

                    if not access_check['allowed']:
                        # Usuario bloqueado o restricción activa
                        messages.error(request, access_check['reason'])
                        logout(request)
                        return redirect('authentication:login')

                    # Si requiere cambio de contraseña
                    if access_check.get('require_password_change', False):
                        # Permitir acceso solo a las URLs de cambio de contraseña
                        allowed_urls = [
                            reverse('user_management:change_my_password'),
                            reverse('authentication:logout'),
                        ]

                        if request.path not in allowed_urls and not request.path.startswith('/static/'):
                            messages.warning(
                                request,
                                'Debes cambiar tu contraseña antes de continuar.'
                            )
                            return redirect('user_management:change_my_password')

                    # Actualizar timestamp de última verificación
                    request.session['last_restriction_check'] = current_time

                # DESHABILITADO: Logging de acceso (genera demasiadas escrituras en BD)
                # Solo habilitar si se necesita auditoría estricta
                # if any(request.path.startswith(path) for path in self.protected_paths):
                #     session_key = f'tracked_access_{request.path}'
                #     if not request.session.get(session_key, False):
                #         from .utils import log_user_action
                #         log_user_action(
                #             request.user,
                #             'system_access',
                #             f'Acceso a: {request.path}',
                #             request
                #         )
                #         request.session[session_key] = True

            except Exception as e:
                logger.error(f"Error en UserTrackingMiddleware: {e}")

        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Middleware para agregar headers de seguridad a las respuestas.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy básica
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://code.jquery.com "
                "https://cdn.datatables.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net "
                "https://cdn.datatables.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
        
        return response


class SessionTimeoutMiddleware:
    """
    Middleware para manejar el timeout de sesiones inactivas.
    Optimizado para actualizar solo cada 30 segundos en lugar de cada request.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Timeout en segundos (30 minutos por defecto)
        self.timeout = getattr(settings, 'SESSION_TIMEOUT', 1800)
        # Intervalo de actualización (30 segundos)
        self.update_interval = 30

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = timezone.now()
            last_activity = request.session.get('last_activity')

            if last_activity:
                # Convertir string a datetime si es necesario
                if isinstance(last_activity, str):
                    last_activity = timezone.datetime.fromisoformat(last_activity)

                # Verificar timeout
                time_since_activity = (current_time - last_activity).total_seconds()

                if time_since_activity > self.timeout:
                    # Sesión expirada por inactividad
                    # NOTA: Logging deshabilitado para mejor rendimiento
                    logout(request)
                    messages.warning(
                        request,
                        'Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.'
                    )
                    return redirect('authentication:login')

                # Solo actualizar si han pasado más de 30 segundos desde la última actualización
                # Esto reduce significativamente las escrituras en la sesión
                if time_since_activity > self.update_interval:
                    request.session['last_activity'] = current_time.isoformat()
                    request.session.modified = True
            else:
                # Primera actividad de la sesión
                request.session['last_activity'] = current_time.isoformat()

        response = self.get_response(request)
        return response