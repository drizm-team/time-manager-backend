FROM python:3.8.6-buster

RUN apt-get update -y
RUN apt-get install -y nginx nginx-extras gcc libsqlite3-dev \
    python3-dev curl ca-certificates mime-support

# Install envsubst
RUN apt-get -y install gettext-base \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN python3.8 -m pip install poetry uwsgi

# Copy apps and related dependencies
WORKDIR /application/
COPY ["pyproject.toml", "poetry.lock", "manage.py", "./"]
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-dev

WORKDIR /application/TimeManagerBackend/
COPY ["TimeManagerBackend", "./"]

# Set envvars
ENV DJANGO_SETTINGS_MODULE TimeManagerBackend.settings.development
ENV NGINX_HOST localhost
ENV NGINX_PORT 8080

WORKDIR /application/.terraform/
COPY ./.terraform .

WORKDIR /application/keys/
COPY ./keys .

WORKDIR /application/

# Migrate & collect static files
RUN python manage.py migrate --no-input && python manage.py collectstatic --no-input

# Entrypoint compiles Nginx config & starts uWSGI
COPY server/nginx-default.conf.template /etc/nginx/conf.d/default.conf.template
COPY server/uwsgi-dev.ini /
COPY docker/docker-entrypoint-dev.sh /
ENTRYPOINT ["/docker-entrypoint-dev.sh"]

CMD ["nginx", "-g", "daemon off;"]
EXPOSE ${NGINX_PORT}
