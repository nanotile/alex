variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "cloud_sql_instance_connection_name" {
  description = "Cloud SQL instance connection name (project:region:instance)"
  type        = string
}

variable "cloud_sql_database" {
  description = "Cloud SQL database name"
  type        = string
  default     = "alex"
}

variable "cloud_sql_user" {
  description = "Cloud SQL database user"
  type        = string
  default     = "alex_admin"
}

variable "cloud_sql_password_secret_name" {
  description = "Name of the secret containing the database password"
  type        = string
  default     = "alex-db-password"
}

variable "bedrock_model_id" {
  description = "AWS Bedrock model ID"
  type        = string
  default     = "us.amazon.nova-pro-v1:0"
}

variable "bedrock_region" {
  description = "AWS Bedrock region"
  type        = string
  default     = "us-west-2"
}

variable "docker_image" {
  description = "Docker image URI for the tagger agent"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "tagger-agent"
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 3
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "cpu" {
  description = "CPU allocation for each instance"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation for each instance"
  type        = string
  default     = "512Mi"
}

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}
