# ============================================================================
# Outputs for Module 0: Foundation
# ============================================================================

output "project_id" {
  description = "GCP Project ID"
  value       = var.gcp_project
}

output "region" {
  description = "GCP Region"
  value       = var.gcp_region
}

output "cloudrun_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloudrun_sa.email
}

output "cloudrun_service_account_name" {
  description = "Name of the Cloud Run service account"
  value       = google_service_account.cloudrun_sa.name
}

output "scheduler_service_account_email" {
  description = "Email of the Cloud Scheduler service account"
  value       = google_service_account.scheduler_sa.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository name for Docker images"
  value       = google_artifact_registry_repository.alex_docker_repo.name
}

output "artifact_registry_repository_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project}/${google_artifact_registry_repository.alex_docker_repo.name}"
}

output "enabled_apis" {
  description = "List of enabled Google Cloud APIs"
  value       = [for api in google_project_service.required_apis : api.service]
}
