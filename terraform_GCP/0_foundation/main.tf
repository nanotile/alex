# ============================================================================
# Module 0: Foundation - GCP Project Setup
# Alex - Agentic Learning Equities eXplainer (GCP Deployment)
# ============================================================================
# This module sets up the foundational GCP infrastructure:
# - Enables required APIs
# - Creates service accounts for Cloud Run and Cloud Scheduler
# - Configures IAM permissions
# ============================================================================

locals {
  project_id = var.gcp_project
  region     = var.gcp_region

  # Required Google Cloud APIs
  required_apis = [
    "run.googleapis.com",                    # Cloud Run
    "sqladmin.googleapis.com",               # Cloud SQL
    "alloydb.googleapis.com",                # AlloyDB
    "aiplatform.googleapis.com",             # Vertex AI
    "secretmanager.googleapis.com",          # Secret Manager
    "storage.googleapis.com",                # Cloud Storage
    "compute.googleapis.com",                # Compute Engine (for networking)
    "servicenetworking.googleapis.com",      # Service Networking
    "cloudtasks.googleapis.com",             # Cloud Tasks
    "cloudscheduler.googleapis.com",         # Cloud Scheduler
    "artifactregistry.googleapis.com",       # Artifact Registry
    "monitoring.googleapis.com",             # Cloud Monitoring
    "logging.googleapis.com",                # Cloud Logging
    "cloudapis.googleapis.com",              # Google Cloud APIs
    "iamcredentials.googleapis.com",         # IAM Service Account Credentials
    "cloudresourcemanager.googleapis.com",   # Cloud Resource Manager
  ]
}

# ============================================================================
# Enable Required APIs
# ============================================================================

resource "google_project_service" "required_apis" {
  for_each = toset(local.required_apis)

  project = local.project_id
  service = each.value

  disable_on_destroy = false

  timeouts {
    create = "30m"
    update = "30m"
  }
}

# ============================================================================
# Service Accounts
# ============================================================================

# Service Account for Cloud Run services
resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.project_name}-cloudrun-sa"
  display_name = "Alex Cloud Run Service Account"
  description  = "Service account for all Alex Cloud Run services (agents, API, researcher)"
  project      = local.project_id

  depends_on = [google_project_service.required_apis]
}

# Service Account for Cloud Scheduler
resource "google_service_account" "scheduler_sa" {
  account_id   = "${var.project_name}-scheduler-sa"
  display_name = "Alex Cloud Scheduler Service Account"
  description  = "Service account for Cloud Scheduler to invoke Cloud Run services"
  project      = local.project_id

  depends_on = [google_project_service.required_apis]
}

# ============================================================================
# IAM Bindings for Cloud Run Service Account
# ============================================================================

# Cloud SQL Client (for database access)
resource "google_project_iam_member" "cloudrun_sql_client" {
  project = local.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Secret Manager Secret Accessor (for database credentials, API keys)
resource "google_project_iam_member" "cloudrun_secret_accessor" {
  project = local.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Vertex AI User (for Gemini and embedding models)
resource "google_project_iam_member" "cloudrun_vertex_user" {
  project = local.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Storage Object Admin (for Cloud Storage buckets - vectors, frontend)
resource "google_project_iam_member" "cloudrun_storage_admin" {
  project = local.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Cloud Tasks Enqueuer (for planner to create agent tasks)
resource "google_project_iam_member" "cloudrun_tasks_enqueuer" {
  project = local.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Cloud Run Invoker (for agent-to-agent communication)
resource "google_project_iam_member" "cloudrun_invoker" {
  project = local.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Logs Writer (for Cloud Logging)
resource "google_project_iam_member" "cloudrun_logs_writer" {
  project = local.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Monitoring Metric Writer (for custom metrics)
resource "google_project_iam_member" "cloudrun_metric_writer" {
  project = local.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# ============================================================================
# IAM Bindings for Cloud Scheduler Service Account
# ============================================================================

# Cloud Run Invoker (to trigger researcher agent)
resource "google_project_iam_member" "scheduler_run_invoker" {
  project = local.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

# ============================================================================
# Artifact Registry Repository
# ============================================================================

resource "google_artifact_registry_repository" "alex_docker_repo" {
  location      = local.region
  repository_id = "${var.project_name}-docker-repo"
  description   = "Docker repository for Alex agent containers"
  format        = "DOCKER"
  project       = local.project_id

  labels = var.labels

  depends_on = [google_project_service.required_apis]
}

# Grant Cloud Run SA permission to pull images
resource "google_artifact_registry_repository_iam_member" "cloudrun_artifact_reader" {
  project    = local.project_id
  location   = google_artifact_registry_repository.alex_docker_repo.location
  repository = google_artifact_registry_repository.alex_docker_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# ============================================================================
# Cloud Storage Bucket for Terraform State (Optional)
# ============================================================================

# Uncomment if you want to migrate to remote state later
# resource "google_storage_bucket" "terraform_state" {
#   name          = "${local.project_id}-terraform-state"
#   location      = local.region
#   force_destroy = false
#
#   uniform_bucket_level_access = true
#
#   versioning {
#     enabled = true
#   }
#
#   labels = var.labels
# }
