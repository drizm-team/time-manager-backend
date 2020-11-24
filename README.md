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
0 */24 * * *

The CloudScheduler Cron must be invoked
through the exodia service account.
