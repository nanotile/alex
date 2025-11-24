output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.tagger_agent.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.tagger_agent.name
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.tagger_agent.location
}

output "test_health_command" {
  description = "Command to test the health endpoint"
  value       = "curl ${google_cloud_run_v2_service.tagger_agent.uri}/health"
}

output "test_tag_command" {
  description = "Example command to test the tag endpoint"
  value       = <<-EOT
    curl -X POST ${google_cloud_run_v2_service.tagger_agent.uri}/tag \
      -H "Content-Type: application/json" \
      -d '{"instruments": [{"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "instrument_type": "etf"}]}'
  EOT
}
