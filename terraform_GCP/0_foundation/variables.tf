# ============================================================================
# Variables for Module 0: Foundation
# ============================================================================

variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "project_name" {
  description = "Project name prefix for resource naming"
  type        = string
  default     = "alex"
}

variable "labels" {
  description = "Common labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "alex"
    managed_by  = "terraform"
    environment = "dev"
  }
}
