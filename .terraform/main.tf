provider "google" {
  credentials = file("../keys/exodia.json")
  region      = "europe-west4"
  zone        = "europe-west4-a"
  project     = var.project_name
}

resource "google_sql_database_instance" "dbf1" {
  name             = var.db_name
  database_version = "POSTGRES_11"
  settings {
    tier = "db-f1-micro"
  }
}

resource "google_sql_database" "database" {
  name     = "time-manager-main-database"
  instance = google_sql_database_instance.dbf1.name
}

resource "google_sql_user" "users" {
  name     = var.db_username
  instance = google_sql_database_instance.dbf1.name
  password = var.db_password
}

resource "google_storage_bucket" "static" {
  name                        = var.static_bucket_name
  location                    = "europe-west4"
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "public_read_static" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
