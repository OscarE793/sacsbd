# sacsbd_project/settings/base.py
# Configuración SACSBD con Metronic/Heon Theme

import os
import sys

# Calcular Raíz del Proyecto (subir 3 niveles desde settings/base.py)
# base.py -> settings -> sacsbd_project -> sacsbd (root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agregar librería local 'holidays' al path (para entornos sin pip)
HOLIDAYS_LIB_PATH = os.path.join(PROJECT_ROOT, 'holidays-dev')
if HOLIDAYS_LIB_PATH not in sys.path:
    sys.path.insert(0, HOLIDAYS_LIB_PATH)



from pathlib import Path
from dotenv import load_dotenv
import sys

# Cargar variables de entorno
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add apps directory to Python path
sys.path.insert(0, str(BASE_DIR / 'apps'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
]

LOCAL_APPS = [
    "apps.authentication",
    "apps.reportes",
    "apps.dashboard",
    "apps.user_management",
    "apps.horas_extras",  # Módulo de gestión de turnos y recargos
    # "apps.server_monitoring",
    # "apps.backup_management",
    # "core",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

ROOT_URLCONF = "sacsbd_project.urls"

# Templates configuración para SACSBD/Heon
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.user_management.context_processors.user_permissions",
                "apps.user_management.context_processors.system_info",
            ],
        },
    },
]

WSGI_APPLICATION = "sacsbd_project.wsgi.application"

# Database - Configuración por defecto (se sobrescribe en development/production)
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": "sacs_bd",
        "USER": "oejaramillop1",
        "PASSWORD": "O2c4r793@J4r4#2065*",
        "HOST": r"DESKTOP-7GB1M4M\SACSBD24",  # Con instancia (raw string)
        "PORT": "",  # Puerto vacío
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
            "extra_params": "TrustServerCertificate=yes;",
        },
    }
}

# Cache configuration - Optimización de rendimiento
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sacsbd-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Máximo de entradas en caché
        },
        'TIMEOUT': 300,  # Timeout por defecto: 5 minutos
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'templates' / 'assets',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Directorios de archivos estáticos
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Finders para archivos estáticos
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Storage configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication URLs
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/reportes/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Session configuration
SESSION_COOKIE_AGE = 1209600  # 2 semanas
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_SAVE_EVERY_REQUEST = False  # OPTIMIZACIÓN: Solo guardar cuando se modifique
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # Usar caché + BD para sesiones

# CSRF protection
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG

# Message framework 

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Configuración SACSBD/Heon
SACSBD_CONFIG = {
    'app_name': 'SACSBD',
    'theme_name': 'Heon',
    'version': '1.0.0',
    'company': 'SACSBD System',
    'description': 'Sistema de Administración y Control de Servidores y Base de Datos',
    'logo_path': 'assets/media/logos/sacsbd-logo.png',
    'favicon_path': 'assets/media/logos/favicon.ico',
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'sacsbd.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Crear directorio de logs si no existe
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Configuración de seguridad para desarrollo
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Configuraciones adicionales para user_management
SESSION_TIMEOUT = 1800  # 30 minutos
SYSTEM_NAME = 'SACSBD'
SYSTEM_VERSION = '1.0.0'
