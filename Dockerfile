FROM python:3.8.6-buster

RUN apt-get update -y
RUN apt-get install -y nginx nginx-extras gcc libsqlite3-dev \
    python3-dev curl ca-certificates mime-support

# Install envsubst
RUN apt-get -y install gettext-base

# Install Poetry and uWSGI
RUN python -m pip install poetry uwsgi

# Copy apps and related dependencies
WORKDIR /application/
COPY ["pyproject.toml", "poetry.lock", "manage.py", "./"]
RUN poetry config virtualenvs.create false
# We may still need APT deps here for buiding wheels
RUN poetry install --no-root --no-dev

RUN apt-get -y autoremove \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /application/TimeManagerBackend/
COPY ["TimeManagerBackend", "./"]

# Set envvars
ENV NGINX_HOST localhost
ENV NGINX_PORT 8080

WORKDIR /application/keys/
COPY ./keys .

WORKDIR /application/.terraform/
COPY ./.terraform .

WORKDIR /application/

# Download statically linked tini
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-static /tini
RUN chmod +x /tini

# Entrypoint compiles Nginx config & starts uWSGI
COPY server/nginx-default.conf.template /etc/nginx/conf.d/default.conf.template
COPY server/uwsgi.ini /
COPY docker/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Wrap the default entrypoint in tini to get a proper PID 1 process
ENTRYPOINT ["/tini", "--", "/docker-entrypoint.sh"]

# Start the nginx process
CMD ["nginx", "-g", "daemon off;"]
EXPOSE ${NGINX_PORT}
# Expose service ports for gRPC connection
EXPOSE 8090/tcp 9090/tcp
