from .production import *  # noqa

# We need to import under different names to avoid clashes,
# with any other storage implementations from production.py
from django.conf.global_settings import (
    STATICFILES_STORAGE as DEFAULT_STATIC_STORAGE,
    DEFAULT_FILE_STORAGE as DEFAULT_FILE_BACKEND
)

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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
DEFAULT_FILE_STORAGE = DEFAULT_FILE_BACKEND
