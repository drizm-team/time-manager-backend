import os
import django
from drizm_commons.utils import Path, Tfvars
from google.oauth2 import service_account

from TimeManagerBackend.docs.settings import *  # noqa
from datetime import timedelta
from .keys import *  # noqa
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = False
TESTING = 'test' in sys.argv  # detect if we are running tests

terraform = Tfvars(
    Path(__file__).parents[2] / ".terraform" / "terraform.tfvars"
)

# All of these are used for the custom GCP-Auth
GCP_CREDENTIALS = Path(__file__).parents[2] / "keys"
GS_CREDENTIALS_FILE = GCP_CREDENTIALS / "exodia_cron.json"
SERVICE_ACCOUNT_GROUP_NAME = "gcp_service_accounts"



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
    'django_prometheus',
    'rest_framework_simplejwt.token_blacklist',

    # Default apps
    'TimeManagerBackend.apps.users',
    'TimeManagerBackend.apps.tokens',

    # User defined apps
    'TimeManagerBackend.apps.events',
    'TimeManagerBackend.apps.notes',
]
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware'
]



""" ORM Config """
CLOUD_SQL_CONN_NAME = f"{terraform.vars.project_name}:" \
                      f"{terraform.vars.project_region}:{terraform.vars.db_service_name}"

DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql_psycopg2',
        'HOST': f"/cloudsql/{CLOUD_SQL_CONN_NAME}",
        'PORT': "5432",
        'NAME': terraform.vars.db_name,
        'USER': terraform.vars.db_username,
        'PASSWORD': terraform.vars.db_password,
    }
}

if os.getenv("MIGRATION_MODE"):
    DATABASES["default"]["HOST"] = "localhost"



""" Auth / Security Config """
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'EXCEPTION_HANDLER':
        'TimeManagerBackend.lib.errors.handler.global_default_exception_handler'  # noqa
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}

ALLOWED_HOSTS = [
    terraform.vars.srv_deploy_domain
]

AUTH_USER_MODEL = 'users.User'



""" CORS Configuration """
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
]
# This applies only to cookies, the integrated system
# is using Header based Token-Auth
CORS_ALLOW_CREDENTIALS = False
# Anything longer than 10 minutes is pointless for REST
CROS_PREFLIGHT_MAX_AGE = 600



""" File Handling Config """
STATIC_URL = '/static/'

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    GS_CREDENTIALS_FILE
)
GS_BUCKET_NAME = terraform.vars.static_bucket_name
GS_PROJECT_ID = terraform.vars.project_name

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "media"),
]



""" Internationlization Config """
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True




""" You probably wont need to touch these """
ROOT_URLCONF = 'TimeManagerBackend.urls'
WSGI_APPLICATION = 'TimeManagerBackend.wsgi.application'

# Without the changes in FORM_RENDERER and TEMPLATE["DIRS"]
# global template directories would not work properly
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



""" Load in the Deployment Settings """
# if we are running on CloudRun, configure stackdriver logging
if os.getenv("GAE_APPLICATION"):
    from google.cloud import logging
    from google.cloud.logging.resource import Resource

    resource_type = 'gae_app'
    resource_labels = {
        'project_id': os.getenv("GOOGLE_CLOUD_PROJECT"),
        'service_id': os.getenv("GAE_DEPLOYMENT_ID"),
        'version_id': os.getenv("GAE_VERSION")
    }

    client = logging.Client().from_service_account_json(GS_CREDENTIALS_FILE)
    # Connects the logger to the root logging handler; by default
    # this captures all logs at INFO level and higher
    client.setup_logging()
    LOGGING = {
        'version': 1,
        'handlers': {
            'stackdriver': {
                'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
                'client': client,
                'resource': Resource(resource_type, resource_labels),
            }
        },
        'loggers': {
            'cloud': {
                'handlers': ['stackdriver'],
                'level': 'DEBUG',
                'name': 'cloud'
            },
            'django': {
                'handlers': ['stackdriver'],
                'level': 'WARNING',
                'propagate': True
            },
            'django.request': {
                'handlers': ['stackdriver'],
                'level': 'WARNING',
            },
        }
    }
