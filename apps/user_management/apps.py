from django.apps import AppConfig


class UserManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user_management'
    verbose_name = 'Gestión de Usuarios'
    
    def ready(self):
        """
        Importa las señales cuando la aplicación está lista.
        """
        try:
            from . import signals
        except ImportError:
            pass