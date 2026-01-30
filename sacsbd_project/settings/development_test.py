# sacsbd_project/settings/development.py
# Configuración para desarrollo con SQL Server - VERSIONES ALTERNATIVAS

import os
from .base import *

# Development-specific settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# ===================================================================
# CONFIGURACIÓN 1: Usando instancia nombrada (ACTUAL)
# ===================================================================
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": "sacs_bd",
        "USER": "oejaramillop1",
        "PASSWORD": "O2c4r793@J4r4#2060*",
        "HOST": "HeonSacsDB",  # Con instancia
        "PORT": "",  # Puerto vacío
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
            "extra_params": "TrustServerCertificate=yes;",
        },
    }
}

# ===================================================================
# CONFIGURACIÓN 2: Usando puerto específico (sin instancia nombrada)
# ===================================================================
DATABASES_CONFIG_2 = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.getenv('DB_NAME', 'sacs_bd'),
        "USER": os.getenv('DB_USER', 'oejaramillop'),
        "PASSWORD": os.getenv('DB_PASSWORD', 'O2c4r793@J4r4#2065*'),
        "HOST": "localhost",
        "PORT": "1433",
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
            "extra_params": "TrustServerCertificate=yes;",
        },
    }
}

# ===================================================================
# CONFIGURACIÓN 3: Usando DSN completo
# ===================================================================
DATABASES_CONFIG_3 = {
    "default": {
        "ENGINE": "mssql",
        "OPTIONS": {
            "dsn": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SACSBD24;DATABASE=sacs_bd;UID=oejaramillop1;PWD=Partmoa588**;TrustServerCertificate=yes;",
        },
    }
}

# ===================================================================
# CONFIGURACIÓN 4: Usando SQLLocalDB (alternativa local)
# ===================================================================
DATABASES_CONFIG_4 = {
    "default": {
        "ENGINE": "mssql",
        "NAME": "sacs_bd",
        "OPTIONS": {
            "dsn": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=(localdb)\\MSSQLLocalDB;DATABASE=sacs_bd;Trusted_Connection=yes;TrustServerCertificate=yes;",
        },
    }
}

# ===================================================================
# CONFIGURACIÓN ACTIVA - Cambia aquí para probar diferentes configuraciones
# ===================================================================
# DATABASES = DATABASES_CONFIG_1  # ← Configuración actual (con instancia)
# DATABASES = DATABASES_CONFIG_2  # ← Probar puerto estándar
# DATABASES = DATABASES_CONFIG_3  # ← Probar DSN directo
# DATABASES = DATABASES_CONFIG_4  # ← Probar LocalDB


# Storage sin compresión para desarrollo
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Debug toolbar para desarrollo (opcional)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
