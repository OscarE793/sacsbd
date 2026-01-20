"""
WSGI config for sacsbd_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/

IMPORTANTE:
- Para desarrollo local: usa 'sacsbd_project.settings.development'
- Para producción (IIS): usa 'sacsbd_project.settings.production'

Puedes cambiar esto configurando la variable de entorno DJANGO_SETTINGS_MODULE
o modificando el valor por defecto aquí.
"""

import os
import sys

# Agregar la carpeta del proyecto al path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Agregar la carpeta apps al path
APPS_DIR = os.path.join(PROJECT_ROOT, 'apps')
if APPS_DIR not in sys.path:
    sys.path.insert(0, APPS_DIR)

from django.core.wsgi import get_wsgi_application

# Configuración por defecto - CAMBIAR A 'production' para desplegar en IIS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacsbd_project.settings.development')

application = get_wsgi_application()
