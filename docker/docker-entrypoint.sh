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

# Configure user and group for uwsgi to run on
uwsgi_user="uwsgi-django"
useradd -G www-data --system --no-create-home "$uwsgi_user"

if [ "${DJANGO_AUTO_SETUP:-0}" == 1 ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
fi

python -m pip install uwsgi  # for some reason we need to install this again
uwsgi /uwsgi.ini --uid "$(id -u $uwsgi_user)" --gid "$(id -g $uwsgi_user)" &
exec "$@"
