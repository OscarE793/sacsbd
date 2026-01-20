# sacsbd_project/settings/production.py
# Configuración de producción para despliegue en IIS

import os
from pathlib import Path
from .base import *

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD - PRODUCCIÓN
# =============================================================================

DEBUG = False

# IMPORTANTE: Cambiar estos valores según tu servidor
# Ejemplo: 'servidor.heon.com.co', '192.168.1.100', 'localhost'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Agregar el nombre del servidor y la IP donde se desplegará
# ALLOWED_HOSTS += ['tu-servidor.dominio.com', '192.168.x.x']

# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS SQL SERVER - PRODUCCIÓN
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.environ.get('DB_NAME', 'sacs_bd'),
        "USER": os.environ.get('DB_USER', 'oejaramillop1'),
        "PASSWORD": os.environ.get('DB_PASSWORD', 'O2c4r793@J4r4#2060'),
        "HOST": os.environ.get('DB_HOST', 'DESKTOP-7GB1M4M\SACSBD24'),
        "PORT": os.environ.get('DB_PORT', ''),
        "OPTIONS": {
            "driver": os.environ.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
            "extra_params": "TrustServerCertificate=yes;",
        },
    }
}

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD HTTPS/SSL
# =============================================================================

# Configuración para HTTPS (descomentar si usas SSL)
# SECURE_SSL_REDIRECT = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS - Solo activar si tienes SSL configurado
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Cookies seguras - Solo si usas HTTPS
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Configuración para HTTP (usar mientras no tengas SSL)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# =============================================================================
# ARCHIVOS ESTÁTICOS - PRODUCCIÓN
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuración de WhiteNoise para servir archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Asegurar que WhiteNoise esté en el middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Debe estar después de SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.user_management.middleware.SecurityHeadersMiddleware",
    "apps.user_management.middleware.UserTrackingMiddleware",
    "apps.user_management.middleware.SessionTimeoutMiddleware",
]

# Configuración de WhiteNoise
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False
WHITENOISE_MAX_AGE = 31536000  # 1 año de cache

# =============================================================================
# ARCHIVOS DE MEDIA
# =============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# LOGGING - PRODUCCIÓN
# =============================================================================

# Crear directorio de logs si no existe
LOGS_DIR = BASE_DIR / 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'sacsbd_production.log',
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'sacsbd_errors.log',
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# =============================================================================
# CONFIGURACIÓN DE CACHE (Opcional - mejora rendimiento)
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# =============================================================================
# CONFIGURACIÓN DE SESIONES
# =============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 28800  # 8 horas
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# =============================================================================
# SECRET KEY - PRODUCCIÓN
# =============================================================================

# IMPORTANTE: Cambiar esta clave en producción
SECRET_KEY = os.environ.get('SECRET_KEY', 'CAMBIAR-ESTA-CLAVE-EN-PRODUCCION-POR-UNA-SEGURA')

# =============================================================================
# CONFIGURACIÓN ADICIONAL PARA IIS
# =============================================================================

# Permitir headers grandes (útil para IIS)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Configuración de CSRF para IIS
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    # Agregar tu dominio aquí:
    # 'https://tu-servidor.dominio.com',
]

print("=" * 60)
print("SACSBD - Configuración de PRODUCCIÓN cargada")
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"Database: {DATABASES['default']['NAME']} @ {DATABASES['default']['HOST']}")
print("=" * 60)
