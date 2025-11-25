output "instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.alex_demo.name
}

output "instance_connection_name" {
  description = "Connection name for Cloud SQL (format: project:region:instance)"
  value       = google_sql_database_instance.alex_demo.connection_name
}

output "database_name" {
  description = "Name of the database"
  value       = google_sql_database.alex.name
}

output "database_user" {
  description = "Database username"
  value       = google_sql_user.alex_admin.name
}

output "database_password_secret" {
  description = "Secret Manager secret containing database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "public_ip" {
  description = "Public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.alex_demo.public_ip_address
}

output "private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.alex_demo.private_ip_address
}

output "setup_instructions" {
  description = "Instructions for next steps"
  value = <<-EOT

  ✅ Cloud SQL Database Deployed!

  Instance: ${google_sql_database_instance.alex_demo.name}
  Connection Name: ${google_sql_database_instance.alex_demo.connection_name}
  Database: ${google_sql_database.alex.name}
  User: ${google_sql_user.alex_admin.name}
  Public IP: ${google_sql_database_instance.alex_demo.public_ip_address}

  NEXT STEPS:

  1. Connect to the database and create schema:

     gcloud sql connect ${google_sql_database_instance.alex_demo.name} \
       --user=${google_sql_user.alex_admin.name} \
       --database=${google_sql_database.alex.name}

     # Get password from Secret Manager:
     gcloud secrets versions access latest --secret=${google_secret_manager_secret.db_password.secret_id}

  2. Run the schema migration:

     # Copy the schema from AWS deployment
     cat /home/kent_benson/AWS_projects/alex/backend/database/migrations/001_initial_schema.sql

     # Apply to GCP Cloud SQL (paste into psql prompt)

  3. Load seed data:

     # Use the same seed data from AWS
     cd /home/kent_benson/AWS_projects/alex/backend/database
     # Adapt seed_data.py to use Cloud SQL connector

  4. Test connection from Python:

     from google.cloud.sql.connector import Connector
     import sqlalchemy

     connector = Connector()

     def getconn():
         return connector.connect(
             "${google_sql_database_instance.alex_demo.connection_name}",
             "pg8000",
             user="${google_sql_user.alex_admin.name}",
             password="<from secret manager>",
             db="${google_sql_database.alex.name}"
         )

     engine = sqlalchemy.create_engine("postgresql+pg8000://", creator=getconn)

  COST ESTIMATE: ~$25-40/month (db-f1-micro tier)

  To pause when not in use:
    gcloud sql instances patch ${google_sql_database_instance.alex_demo.name} --activation-policy=NEVER

  To resume:
    gcloud sql instances patch ${google_sql_database_instance.alex_demo.name} --activation-policy=ALWAYS

  EOT
}
