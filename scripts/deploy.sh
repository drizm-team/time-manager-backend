#!/bin/bash
export DJANGO_SETTINGS_MODULE=TimeManagerBackend.settings.production
export MIGRATION_MODE=1
source "$(dirname "$0")"/common.sh

if [ "$1" = "--initial" ]; then
  tfenv use
  (
  cd ./.terraform || exit
  terraform init
  terraform fmt
  terraform plan -out="./terraform.plan"
  echo "In case anything about the plan is wrong, you can quit now."
  echo "To quit, press Enter, type anything to proceed."
  read -r escape
  if [ -z "$escape" ]; then exit 0; fi
  terraform apply "./terraform.plan"
  )
fi

printf "Attempting Migrations and Staticfile collection...\n"

conn_string=$(django_settings CLOUD_SQL_CONN_NAME)

~/cloud_sql_proxy -instances="$conn_string"=tcp:5432 &
pid=$!
# Give the proxy some time to connect
sleep 5

poetry run python manage.py migrate --no-input
poetry run python manage.py collectstatic --no-input

kill $pid

make requirements
gcloud app deploy --quiet

exit 0
