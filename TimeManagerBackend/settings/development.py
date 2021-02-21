import uuid

# We need to import under different names to avoid clashes,
# with any other storage implementations from production.py
from django.conf.global_settings import (
    STATICFILES_STORAGE as DEFAULT_STATIC_STORAGE,
    DEFAULT_FILE_STORAGE as DEFAULT_FILE_BACKEND
)

from .production import *  # noqa

DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DJANGO_DB_NAME', 'default'),
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': os.getenv('DJANGO_DB_HOST', 'localhost'),
        'PORT': '5432',
    }
}

FIRESTORE_DATABASES = {
    'default': {
        'HOST': 'localhost',
        'PORT': '8080',
    }
}

MIDDLEWARE = [
    # Activate CORS
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # Let all CSRF checks pass that pass CORS
    'corsheaders.middleware.CorsPostCsrfMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_REPLACE_HTTPS_REFERER = True

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = [
    "127.0.0.1"
]
ALLOWED_HOSTS = ["*"]

# Just so any changes to e.g. external file storage,
# do not affect our development server
STATIC_URL = '/static/'
STATIC_ROOT = '/var/django/projects/TimeManagerBackend/static/'  # noqa

STATICFILES_STORAGE = DEFAULT_STATIC_STORAGE

if DEBUG and TESTING:
    GS_BUCKET_NAME = f"{uuid.uuid4()}__test_bucket"

if DEBUG and not TESTING:
    DEFAULT_FILE_STORAGE = DEFAULT_FILE_BACKEND
