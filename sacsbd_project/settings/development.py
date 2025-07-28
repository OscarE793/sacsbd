# sacsbd_project/settings/development.py
# Configuración para desarrollo con SQL Server

import os
from .base import *

# Development-specific settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# SQL Server Database Configuration para Desarrollo
# CONFIGURACIÓN CORREGIDA PARA INSTANCIA SACSBD24 (CONFIRMADA FUNCIONANDO)

# DESCOMENTA ESTA LÍNEA PARA USAR SQLITE TEMPORALMENTE:
# DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

# CONFIGURACIÓN SQL SERVER PARA SACSBD24 (ACTIVA):
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": "sacs_bd",
        "USER": "oejaramillop1",
        "PASSWORD": "Partmoa588**",
        "HOST": "DESKTOP-7GB1M4M\\SACSBD24",  # Con instancia
        "PORT": "",  # Puerto vacío
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
            "extra_params": "TrustServerCertificate=yes;",
        },
    }
}

# Storage sin compresión para desarrollo
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",  # Sin compresión
    },
}

# Debug toolbar para desarrollo (opcional)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']


