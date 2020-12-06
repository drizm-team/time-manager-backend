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
}

resource "google_storage_bucket_iam_member" "public_read_static" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

/*
Service config
*/
resource "google_cloud_run_service" "default" {
  name     = var.srv_service_name
  location = var.project_region

  template {
    spec {
      containers {
        image = var.srv_image_name
      }
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = terraform.workspace == "stag" ? 5 : 25
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.dbf1.connection_name
        "run.googleapis.com/client-name"        = var.srv_service_name
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.default.location
  project  = google_cloud_run_service.default.project
  service  = google_cloud_run_service.default.name

  policy_data = data.google_iam_policy.noauth.policy_data

  depends_on = [
    google_cloud_run_service.default
  ]
}

resource "google_cloud_run_domain_mapping" "default" {
  location = var.project_region
  name     = var.srv_deploy_domain

  metadata {
    namespace = var.project_name
    annotations = {
      "run.googleapis.com/launch-stage" = "BETA"
    }
  }

  spec {
    route_name = google_cloud_run_service.default.name
  }

  depends_on = [
    google_cloud_run_service.default
  ]
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
