variable "gcp_project" {
  description = "GCP Project ID where resources will be deployed"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for resources"
  type        = string
}

variable "embedding_model_name" {
  description = "Name of the Vertex AI embedding model to use"
  type        = string
  default     = "text-embedding-004"  # Google's latest text embedding model
}

variable "project_name" {
  description = "Project name prefix for resource naming"
  type        = string
  default     = "alex-gcl"
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "alex-gcl"
    managed_by  = "terraform"
    environment = "dev"
  }
}
