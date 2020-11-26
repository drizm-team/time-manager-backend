// General config
variable "project_name" {
  type        = string
  description = "Name of the Project the infrastructure is going to be provisioned in"
}

variable "project_region" {
  type        = string
  description = "Region that all resources are going to be provisioned in"
}

variable "project_admin" {
  type        = string
  description = "Email Address of the administrative project service account"
}

// Database config
variable "db_password" {
  type        = string
  description = "Password for the root user of the database"
}

variable "db_username" {
  type        = string
  description = "Root user of the database"
}

variable "db_service_name" {
  type        = string
  description = "Name of the database on Google Cloud"
}

variable "db_name" {
  type        = string
  description = "Name of the actual SQL database"
}

// Bucket config
variable "static_bucket_name" {
  type        = string
  description = "Name of the bucket that holds the staticfiles for the Django project"
}

variable "state_bucket_name" {
  type        = string
  description = "Name of the bucket that holds the remote state of Terraform"
}

// CloudRun config
variable "srv_service_name" {
  type        = string
  description = "Name of the CloudRun service that this project is going to be deployed as"
}

variable "srv_deploy_domain" {
  type        = string
  description = "Domain that the CloudRun service is going to be deployed on"
}

variable "srv_image_name" {
  type        = string
  description = "FQDN of the image that will be used to generate the CloudRun service instances"
}
