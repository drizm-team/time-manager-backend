import os

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

if os.getenv("MIGRATION_MODE"):
    DATABASES["default"]["HOST"] = "localhost"
