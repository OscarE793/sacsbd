import os
from .base import *

# Production-specific settings
DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SQL Server Database configuration for production
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

WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True if DEBUG else False