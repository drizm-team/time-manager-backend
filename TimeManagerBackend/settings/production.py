import os
import sys
from datetime import timedelta

import django
from drizm_commons.utils import Tfvars, Path
from google.oauth2 import service_account

from TimeManagerBackend.docs.settings import *  # noqa
from .keys import *  # noqa

TESTING = 'test' in sys.argv  # detect if we are running tests

terraform = Tfvars(
    Path(__file__).parents[2] / ".terraform" / "terraform.tfvars"
)

# Both of these are used for the custom GCP-Auth
GCP_CREDENTIALS = Path(__file__).parents[2] / "keys"
SERVICE_ACCOUNT_GROUP_NAME = "gcp_service_accounts"

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
    'rest_framework_simplejwt.token_blacklist',

    # User defined apps
    'TimeManagerBackend.apps.errors',
    'TimeManagerBackend.apps.users',
    'TimeManagerBackend.apps.notes'
]

CLOUD_SQL_CONN_NAME = f"{terraform.vars.project_name}:" \
                      f"{terraform.vars.project_region}:{terraform.vars.db_service_name}"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': f"/cloudsql/{CLOUD_SQL_CONN_NAME}",
        'PORT': "5432",
        'NAME': terraform.vars.db_name,
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

GS_CREDENTIALS_FILE = Path(__file__).parents[2] / "keys" / "exodia_cron.json"
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    GS_CREDENTIALS_FILE
)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "media"),
]

DEBUG = False
AUTH_USER_MODEL = 'users.User'

ALLOWED_HOSTS = [
    terraform.vars.srv_deploy_domain
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

# if we are running on CloudRun, configure stackdriver logging
if os.getenv("K_SERVICE"):
    from google.cloud import logging

    client = logging.Client().from_service_account_json(GS_CREDENTIALS_FILE)
    # Connects the logger to the root logging handler; by default
    # this captures all logs at INFO level and higher
    client.setup_logging()
    LOGGING = {
        'version': 1,
        'handlers': {
            'stackdriver': {
                'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
                'client': client
            }
        },
        'loggers': {
            'cloud': {
                'handlers': ['stackdriver'],
                'level': 'INFO',
                'name': "cloud"
            },
            'django.request': {
                'handlers': ['stackdriver'],
                'level': 'WARN',
            },
        }
    }
