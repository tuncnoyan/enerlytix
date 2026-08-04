"""
Django settings for Enerlytix project.
"""

import os
from urllib.parse import urlparse, unquote
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Build paths inside the Django app project like this: BASE_DIR / 'subdir'.
# This must resolve to the folder containing manage.py in both local and Docker runs.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'anymail',
    'rest_framework',
    'sitesync',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

database_url = os.getenv('DATABASE_URL')
if database_url:
    parsed_url = urlparse(database_url)
    if parsed_url.scheme in ('postgresql', 'postgres'):
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_url.path.lstrip('/'),
            'USER': unquote(parsed_url.username or ''),
            'PASSWORD': unquote(parsed_url.password or ''),
            'HOST': parsed_url.hostname or '',
            'PORT': parsed_url.port or 5432,
            'OPTIONS': {
                'sslmode': os.getenv('DATABASE_SSLMODE', 'require' if not DEBUG else 'prefer'),
            },
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
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Use the app login page for authenticated views that require sign-in.
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': int(os.getenv('PAGE_SIZE', 50)),
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'sitesync': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Etainabl API Configuration
ETAINABL_API_KEY = os.getenv('ETAINABL_API_KEY')
ETAINABL_API_URL = os.getenv('ETAINABL_API_URL', 'https://api.etainabl.com/2.0')
ETAINABL_ACCOUNT_ID = os.getenv('ETAINABL_ACCOUNT_ID', '6584fdd1c9ec4255')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))

# Usage and invoice import configuration
CONSUMPTION_RETENTION_MONTHS = int(os.getenv('CONSUMPTION_RETENTION_MONTHS', 36))
CONSUMPTION_IMPORT_RETRY_COUNT = int(os.getenv('CONSUMPTION_IMPORT_RETRY_COUNT', 1))
CONSUMPTION_IMPORT_RETRY_BACKOFF_SECONDS = int(os.getenv('CONSUMPTION_IMPORT_RETRY_BACKOFF_SECONDS', 2))
CONSUMPTION_HALFHOURLY_MONTHS = int(os.getenv('CONSUMPTION_HALFHOURLY_MONTHS', 2))
CONSUMPTION_MONTHLY_MONTHS = int(os.getenv('CONSUMPTION_MONTHLY_MONTHS', 24))
CONSUMPTION_INVOICE_MONTHS = int(os.getenv('CONSUMPTION_INVOICE_MONTHS', 12))

# Email configuration
MAILTRAP_API_TOKEN = (os.getenv('MAILTRAP_API_TOKEN') or '').strip()
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'hello@demomailtrap.co')
MAIL_REPLY_TO = os.getenv('MAIL_REPLY_TO', '')
MAILTRAP_EMAIL_BACKEND = 'anymail.backends.mailtrap.EmailBackend'

if MAILTRAP_API_TOKEN:
    ANYMAIL = {
        'MAILTRAP_API_TOKEN': MAILTRAP_API_TOKEN,
    }
    CONFIGURED_EMAIL_BACKEND = MAILTRAP_EMAIL_BACKEND
else:
    ANYMAIL = {}
    CONFIGURED_EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

EMAIL_BACKEND = CONFIGURED_EMAIL_BACKEND

# Security Settings
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# Enforce TLS/HTTPS in production when explicitly configured.
# Keep the default disabled during tests and local development unless the environment requests it.
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True'
    SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'True') == 'True'

# Ensure logs directory exists
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
