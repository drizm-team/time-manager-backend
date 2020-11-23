variable "db_password" {
  type = string
  description = "Password for the root user of the database"
}

variable "db_username" {
  type = string
  description = "Root user of the database"
}

variable "db_name" {
  type = string
  description = "Name of the database"
}

variable "project_name" {
  type = string
  description = "Name of the Project the infrastructure is going to be provisioned in"
}

variable "static_bucket_name" {
  type = string
  description = "Name of the bucket that holds the staticfiles for the Django project"
}
