terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Cloud SQL PostgreSQL Instance (Minimal Tier for Demo)
resource "google_sql_database_instance" "alex_demo" {
  name             = "alex-demo-db"
  database_version = "POSTGRES_15"
  region           = var.gcp_region
  project          = var.gcp_project

  settings {
    # Minimal tier - shared CPU, 0.6GB RAM (~$25-40/month)
    tier = "db-f1-micro"

    # Storage configuration
    disk_type = "PD_SSD"
    disk_size = 10  # Minimal 10GB

    # Backup configuration
    backup_configuration {
      enabled            = true
      start_time         = "03:00"
      point_in_time_recovery_enabled = false  # Save cost
    }

    # IP configuration - using public IP for simplicity
    ip_configuration {
      ipv4_enabled = true

      # Allow access from anywhere initially (will restrict after testing)
      authorized_networks {
        name  = "allow-all-for-demo"
        value = "0.0.0.0/0"
      }
    }

    # Maintenance window
    maintenance_window {
      day          = 7  # Sunday
      hour         = 3
      update_track = "stable"
    }
  }

  # Allow deletion without protection (for demo/learning)
  deletion_protection = false
}

# Create the alex database
resource "google_sql_database" "alex" {
  name     = "alex"
  instance = google_sql_database_instance.alex_demo.name
  project  = var.gcp_project
}

# Create database user
resource "google_sql_user" "alex_admin" {
  name     = "alex_admin"
  instance = google_sql_database_instance.alex_demo.name
  password = random_password.db_password.result
  project  = var.gcp_project
}

# Store database password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "alex-demo-db-password"
  project   = var.gcp_project

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Grant Cloud Run service account access to the secret
resource "google_secret_manager_secret_iam_member" "cloudrun_secret_access" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloudrun_service_account_email}"
}
