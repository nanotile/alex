# Cloud Run service for Tagger agent
resource "google_cloud_run_v2_service" "tagger_agent" {
  name                = var.service_name
  location            = var.gcp_region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false  # Allow updates via terraform

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.docker_image

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # Environment variables for the service
      env {
        name  = "VERTEX_MODEL_ID"
        value = var.vertex_model_id
      }

      env {
        name  = "VERTEX_PROJECT"
        value = var.gcp_project
      }

      env {
        name  = "VERTEX_LOCATION"
        value = var.gcp_region
      }

      env {
        name  = "CLOUD_SQL_INSTANCE"
        value = var.cloud_sql_instance_connection_name
      }

      env {
        name  = "CLOUD_SQL_DATABASE"
        value = var.cloud_sql_database
      }

      env {
        name  = "CLOUD_SQL_USER"
        value = var.cloud_sql_user
      }

      # Get password from Secret Manager
      env {
        name = "CLOUD_SQL_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = var.cloud_sql_password_secret_name
            version = "latest"
          }
        }
      }
    }

    timeout = "${var.timeout_seconds}s"
  }

  # Allow service account to access Cloud SQL
  lifecycle {
    ignore_changes = [
      template[0].revision,
    ]
  }
}

# IAM binding to allow unauthenticated access (for demo purposes)
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  count = var.allow_unauthenticated ? 1 : 0

  location = google_cloud_run_v2_service.tagger_agent.location
  name     = google_cloud_run_v2_service.tagger_agent.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Grant the Cloud Run service account access to Secret Manager
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_access" {
  secret_id = var.cloud_sql_password_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant the Cloud Run service account access to Cloud SQL
resource "google_project_iam_member" "cloud_run_sql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Grant the Cloud Run service account access to Vertex AI
resource "google_project_iam_member" "cloud_run_vertex_user" {
  project = var.gcp_project
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Data source to get project number
data "google_project" "project" {
  project_id = var.gcp_project
}
