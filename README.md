# Time Manager Backend

This is the repository for the backend
for the time-manager project.

The project can currently be found at:
https://api.chrono.drizm.com/

Current live version (Commit hash):  
c0e8f671

Install dependencies:  
``make``

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

## Deployment

### Prerequisites

- Docker Desktop installed
- Access to GCP Console

**The following locations contain keys:**
- ./keys/
- ./TimeManagerBackend/settings/keys.py
- ./.terraform/terraform.tfvars
- ./.firebasekey

#### keys folder Contents

The "keys" directory contains the .json
keys for Google Cloud Platform service
accounts.  
By default, this project will expect a user
called **exodia_cron**.  
This user is required, but you can add
additional ones if wanted.

All users added to this folder will
qualify to request to management
endpoints once the Migrations have run!  

See the respective project for a key.

#### keys.py Contents

SECRET_KEY = str  
PROM_USER = str(email)  
PROM_PASSWORD = str  

#### terraform.tfvars Contents

For the contents here, see the
variables.tf file.  
All variables listed in that file need to
be present here.

Example Syntax:
key = "string-value"
key2 = "another-string-value"

Once everything is done, simply run:  
``cd docker``  
``docker-compose up --build``

#### .firebasekey Contents

For this you simply need to run
``firebase login:ci``.
You then copy the resulting key
into the ``.firebasekey`` file.

## Deployment

### Prerequsites

- Gsutil, Gcloud, CloudSDK
- CloudSQL Proxy
- Bash + WSL / Debian Linux
- Tfenv (Terraform)
- Access to GCP project via CLI
- Auth credentials for project in CLI

For initial deployment:  
``make deploy_initial``  

For refresh deployments:  
``make deploy_refresh``

To completely reset and
update a deployment:  
``make deploy_reset``

## Documentation

Setting for keys-folder:  
GCP_CREDENTIALS = Path
