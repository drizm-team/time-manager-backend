import uuid
import os

from google.auth.credentials import AnonymousCredentials

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
        'PORT': '8090',
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

# Save all FileField and ImageField files to GCS
DEFAULT_FILE_STORAGE = 'TimeManagerBackend.lib.commons.gcs.EmulatedGCS'

# Save all 'collectstatic' files to GCS
STATICFILES_STORAGE = 'TimeManagerBackend.lib.commons.gcs.EmulatedGCS'

GS_CUSTOM_ENDPOINT = os.environ.get(
    "STATIC_CUSTOM_COLLECTION_ENDPOINT", "https://localhost:4443"
)
GS_CREDENTIALS = AnonymousCredentials()
GS_PROJECT_ID = "test"
GS_BUCKET_NAME = "test"
