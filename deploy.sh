#!/bin/bash
export DJANGO_SETTINGS_MODULE=TimeManagerBackend.settings.production
export MIGRATION_MODE=1

printf "Attempting Migrations and Staticfile collection...\n"

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

# Change the --tag value if necessary
gcloud builds submit --tag gcr.io/time-manager-295921/time-manager-backend --timeout=3600

project_id="$(gcloud config get-value project)"
project_number=$(gcloud projects list \
  --filter="$project_id" \
  --format="value(PROJECT_NUMBER)")

echo -e "Applying IAM-Policy Bindings for User Agent...\n"
gcloud projects add-iam-policy-binding "$project_id" \
  --member serviceAccount:service-"$project_number"@gcp-sa-cloudscheduler.iam.gserviceaccount.com \
  --role roles/cloudscheduler.serviceAgent

tfenv use
# shellcheck disable=SC2164
cd ./.terraform
terraform get
terraform fmt

if [[ "$1" == "--initial" ]]; then
  terraform plan -out="./terraform.plan"
  echo "In case anything about the plan is wrong, you can quit now."
  echo "To quit, press Enter, type anything to proceed."
  read -r escape
  if [ -z "$escape" ]; then exit 0; fi
  terraform apply "./terraform.plan"
else
  echo "No valid args provided, only recreating the CloudRun service"
  # Just list all services here that need to be refreshed everytime
  terraform taint google_cloud_run_service.default
  terraform plan -out="./terraform.plan"
  terraform apply "./terraform.plan"
fi

exit 0
