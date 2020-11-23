#!/bin/bash
export DJANGO_SETTINGS_MODULE=TimeManagerBackend.settings.production
export MIGRATION_MODE=1

command="poetry run python <<< 'from django.conf import settings; print(settings.CLOUD_SQL_CONN_NAME)'"
eval "$command" > ./test.log
conn_string=$(cat ./test.log)
rm -rf ./test.log

~/cloud_sql_proxy -instances="$conn_string"=tcp:5432 &
pid=$!

poetry run python manage.py migrate --no-input
poetry run python manage.py collectstatic --no-input

rm -rf static
kill %"$pid"

gcloud builds submit --tag gcr.io/time-manager-295921/time-manager-backend --timeout=3600

gcloud run deploy time-manager-backend --image gcr.io/time-manager-295921/time-manager-backend \
--platform managed \
--region europe-west4  \
--allow-unauthenticated \
--add-cloudsql-instances time-manager-backend-db

exit 0
