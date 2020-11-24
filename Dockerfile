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
ENV DJANGO_SETTINGS_MODULE TimeManagerBackend.settings.production
ENV NGINX_HOST localhost
ENV NGINX_PORT 8080

WORKDIR /application/.terraform/
COPY ./.terraform .

WORKDIR /application/keys/
COPY ./keys .

WORKDIR /application/

# Entrypoint compiles Nginx config & starts uWSGI
COPY server/nginx-default.conf.template /etc/nginx/conf.d/default.conf.template
COPY server/uwsgi.ini /
COPY docker/docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["nginx", "-g", "daemon off;"]
EXPOSE ${NGINX_PORT}
