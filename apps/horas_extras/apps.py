# apps/horas_extras/apps.py
from django.apps import AppConfig


class HorasExtrasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.horas_extras'
    verbose_name = 'Horas Extras y Recargos'
    
    def ready(self):
        # Importar señales si las necesitamos
        try:
            import apps.horas_extras.signals
        except ImportError:
            pass
