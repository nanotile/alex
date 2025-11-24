variable "gcp_project" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "cloudrun_service_account_email" {
  description = "Email of the Cloud Run service account (from Module 0)"
  type        = string
}
