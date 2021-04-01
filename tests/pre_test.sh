#!/bin/bash
set -eu

compose_namespace="timemanagertests"

# Remove services from previous tests
(
cd docker || exit 127
docker-compose -p "$compose_namespace" \
  down --volumes
)

# Create the test bucket for the GCS-server
source scripts/common.sh
mkdir -p "docker/test-gcs-data/$(django_settings GS_BUCKET_NAME)"

# Start all services required for testing
(
cd docker || exit 127
docker-compose -p "$compose_namespace" \
  -f docker-compose.yml \
  -f docker-compose.test.yml \
  up --build --detach
)

# Give the systems time to start up
sleep 5
