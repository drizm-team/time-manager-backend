import os
import django
from google.oauth2 import service_account

from TimeManagerBackend.docs.settings import *  # noqa
from datetime import timedelta
from drizm_commons.utils import Tfvars, Path
from .keys import *  # noqa

terraform = Tfvars(
    Path(__file__).parents[2] / ".terraform" / "terraform.tfvars"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLED_APPS = [
    'drizm_django_commons',  # manage.py overrides
    'TimeManagerBackend.application.CustomAdmin',  # default admin
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'drf_yasg',
    'corsheaders',

    # User defined apps
    'TimeManagerBackend.apps.errors',
    'TimeManagerBackend.apps.users',
    'TimeManagerBackend.apps.notes'
]

CLOUD_SQL_CONN_NAME = "time-manager-295921:europe-west4:time-manager-backend-db"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': f"/cloudsql/{CLOUD_SQL_CONN_NAME}",
        'PORT': "5432",
        'NAME': "time-manager-main-database",
        'USER': terraform.vars.db_username,
        'PASSWORD': terraform.vars.db_password,
    }
}

# In case we are currently in migration mode
if os.getenv("MIGRATION_MODE"):
    DATABASES["default"]["HOST"] = "localhost"

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'EXCEPTION_HANDLER':
        'TimeManagerBackend.apps.errors.handler.global_default_exception_handler'
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATIC_URL = '/static/'
GS_BUCKET_NAME = terraform.vars.static_bucket_name
GS_PROJECT_ID = terraform.vars.project_name
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    Path(__file__).parents[2] / "keys" / "exodia.json"
)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "media"),
]

DEBUG = False
AUTH_USER_MODEL = 'users.User'

ALLOWED_HOSTS = [
    "api.chrono.drizm.com"
]

# CORS Configuration
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]
CORS_EXPOSE_HEADERS = [
    "Content-Disposition"
]
CORS_ALLOWED_ORIGINS = [
    "https://chrono.drizm.com",
    "https://api.chrono.drizm.com"
]
CORS_ALLOW_CREDENTIALS = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'TimeManagerBackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates"),
            os.path.join(django.__path__[0] + '/forms/templates'),
        ],
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

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'TimeManagerBackend.wsgi.application'

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
