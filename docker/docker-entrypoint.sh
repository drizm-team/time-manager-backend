#!/bin/bash
set -eu

# In case we are running on Google Cloud Run, overwrite the config value
port=${PORT:-"$NGINX_PORT"}

export NGINX_PORT=${port:-8080}
export NGINX_HOST=${NGINX_HOST:-localhost}

# shellcheck disable=SC2016
envsubst '${NGINX_PORT} ${NGINX_HOST}' < \
  /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Own the application and static directories,
# as well as the uwsgi.ini file to the nginx group
# This way both nginx and uwsgi can access the applications files
locations=("/application" "/uwsgi.ini")

for location in "${locations[@]}"; do
  chmod -R 770 "$location"
  chown -R root:www-data "$location"
done

# Create the user and group that uwsgi will run on
# Only create the user if it does not already exist
uwsgi_user="uwsgi-django"
id -u "$uwsgi_user" &> /dev/null || \
  useradd -G www-data --system --no-create-home "$uwsgi_user"

if [ "${DJANGO_AUTO_SETUP:-0}" == 1 ]; then
  echo 'Waiting for Service Startup.'
  sleep 5  # we need to wait for the db to start up
  python manage.py migrate --noinput

  if [[ "$DJANGO_SETTINGS_MODULE" == *development ]]; then
    echo 'Running in Development-Mode, configuring static-file collection.'
    export STATIC_CUSTOM_COLLECTION_ENDPOINT="https://cloud-storage:4443"
    python manage.py collectstatic --noinput
    unset STATIC_CUSTOM_COLLECTION_ENDPOINT
  fi
fi

python -m pip install uwsgi  # for some reason we need to install this again
uwsgi /uwsgi.ini --uid "$(id -u $uwsgi_user)" --gid "$(id -g $uwsgi_user)" &
exec "$@"
