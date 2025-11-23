# ============================================================================
# Shared Variables for GCP Terraform Modules
# Alex - Agentic Learning Equities eXplainer (GCP Deployment)
# ============================================================================

variable "gcp_project" {
  description = "GCP Project ID where resources will be deployed"
  type        = string
}

variable "gcp_region" {
  description = "Primary GCP region for resource deployment"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "GCP zone within the region"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
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

# Vertex AI Configuration
variable "vertex_model_id" {
  description = "Vertex AI model ID for LLM inference"
  type        = string
  default     = "gemini-1.5-pro"
}

variable "vertex_embeddings_model" {
  description = "Vertex AI embeddings model"
  type        = string
  default     = "textembedding-gecko@003"
}

# Database Configuration
variable "db_tier" {
  description = "Database instance tier"
  type        = string
  default     = "db-custom-2-7680" # 2 vCPU, 7.68 GB RAM
}

variable "db_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_15"
}

# Monitoring
variable "enable_monitoring" {
  description = "Enable Cloud Monitoring dashboards and alerts"
  type        = bool
  default     = true
}
