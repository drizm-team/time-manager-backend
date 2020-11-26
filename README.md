# Time Manager Backend

This is the repository for the backend
for the time-manager project.

The project can currently be found at:
https://api.chrono.drizm.com/

## Related Infrastructure

This project requires the following
infrastructure:
- Static Content Bucket
- CloudSQL Postgres Database
- Cloud Run Service
- CloudRegistry Container
- CloudScheduler Cron

CloudScheduler Cron frequency:
0 0 * * *

The CloudScheduler Cron must be invoked
through the exodia service account.

## Local Deployment

### Prerequisites

- Docker Desktop installed
- Access to GCP Console

For local development, the following steps
need to be taken:
- Add keys folder at project root
- Add exodia.json to afor mentioned folder,
containing the service-account key for the
super-admin of the project (exodia_cron)
- Add TimeManagerBackend/settings/keys.py
file, containing SECRET_KEY = "<some-value>"
- In the .terraform directory, add a new
file called terraform.tfvars, containing
values for all the variables in the
variables.tf file.

Once everything is done, simply run:  
``cd docker``  
``docker-compose up --build``

## Deployment

### Prerequsites

- Gsutil, Gcloud, CloudSDK
- CloudSQL Proxy
- Bash + WSL / Debian Linux
- Tfenv (Terraform)
- Access to GCP project via CLI
- Auth credentials for project in CLI

For initial deployment:  
``bash deploy.sh --initial``  

For refresh deployments:  
``bash.deploy.sh``
