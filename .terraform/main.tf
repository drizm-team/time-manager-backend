terraform {
  backend "gcs" {
    bucket      = "time-manager-backend-tf-state"
    credentials = "../keys/exodia_cron.json"
  }
}

provider "google" {
  credentials = file("../keys/exodia_cron.json")
  region      = var.project_region
  zone        = "${var.project_region}-a"
  project     = var.project_name
}

/*
Database config
*/
resource "google_sql_database_instance" "dbf1" {
  name             = var.db_service_name
  database_version = "POSTGRES_11"
  settings {
    tier = "db-f1-micro"
  }
}

resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.dbf1.name
}

resource "google_sql_user" "users" {
  name     = var.db_username
  instance = google_sql_database_instance.dbf1.name
  password = var.db_password
}

/*
Bucket config
*/
resource "google_storage_bucket" "static" {
  name                        = var.static_bucket_name
  location                    = upper(var.project_region)
  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_storage_bucket_iam_member" "public_read_static" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

/*
Cronjobs
*/
resource "google_cloud_scheduler_job" "flush_expired_job" {
  name             = "flush-expired-tokens"
  description      = "Every 24hrs, flushes expired RefreshTokens off the blacklist"
  schedule         = "0 0 * * *"
  time_zone        = "Europe/London"
  attempt_deadline = "120s"
  region           = "europe-west3"

  http_target {
    http_method = "POST"
    uri         = "https://${var.srv_deploy_domain}/users/__flush_expired__/"

    oidc_token {
      service_account_email = var.project_admin
    }
  }
}
