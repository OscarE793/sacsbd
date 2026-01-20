"""
WSGI config for SACSBD project - PRODUCCIÓN (IIS)

Este archivo es específico para el despliegue en IIS con wfastcgi.
"""

import os
import sys

# Agregar la ruta del proyecto al path de Python
# IMPORTANTE: Cambiar esta ruta según tu instalación
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Agregar la carpeta apps al path
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))

# Configurar el módulo de settings para producción
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacsbd_project.settings.production')

# Cargar variables de entorno desde .env.production si existe
env_file = os.path.join(PROJECT_ROOT, '.env.production')
if os.path.exists(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
