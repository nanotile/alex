output "embedding_model_name" {
  description = "Name of the Vertex AI embedding model"
  value       = var.embedding_model_name
}

output "vertex_ai_location" {
  description = "Location for Vertex AI API calls"
  value       = var.gcp_region
}

output "vertex_ai_endpoint" {
  description = "Vertex AI API endpoint URL"
  value       = "https://${var.gcp_region}-aiplatform.googleapis.com"
}

output "embedding_dimensions" {
  description = "Number of dimensions in the embedding vectors"
  value       = 768  # text-embedding-004 produces 768-dimensional vectors
}

output "setup_instructions" {
  description = "Instructions for using Vertex AI embeddings"
  value = <<-EOT

    ✅ Vertex AI Embeddings configuration complete!

    IMPORTANT DIFFERENCES FROM AWS:
    ════════════════════════════════════════════════════════════════

    GCP uses a managed API approach - NO endpoint deployment needed!

    • AWS SageMaker: Deploy endpoint → Wait 5 min → Invoke endpoint
    • GCP Vertex AI: Call API directly → Instant usage

    COST COMPARISON:
    ────────────────
    • AWS SageMaker Serverless: ~$1-2/month + per-second compute
    • GCP Vertex AI Embeddings: Pay-per-use only ($0.025/1000 characters)

    EMBEDDING DIMENSIONS:
    ─────────────────────
    • AWS (all-MiniLM-L6-v2): 384 dimensions
    • GCP (text-embedding-004): 768 dimensions

    ⚠️  Note: Vector dimension change means AWS and GCP vectors are NOT compatible!

    TO USE IN PYTHON:
    ─────────────────

    1. Install the library:
       uv add google-cloud-aiplatform

    2. Add to your .env.gcp:
       GCP_PROJECT=${var.gcp_project}
       GCP_REGION=${var.gcp_region}
       VERTEX_EMBEDDING_MODEL=${var.embedding_model_name}

    3. Use the example code:
       See: terraform_GCP/2_embeddings/python_usage_example.py

    4. Test it:
       python -c "from vertexai.language_models import TextEmbeddingModel; import vertexai; vertexai.init(project='${var.gcp_project}', location='${var.gcp_region}'); model = TextEmbeddingModel.from_pretrained('${var.embedding_model_name}'); result = model.get_embeddings(['test']); print(f'Success! Generated {len(result[0].values)} dimensional vector')"

    PRICING DETAILS:
    ────────────────
    • First 1 million characters/month: $0.025 per 1000 characters
    • Beyond 1 million: $0.0125 per 1000 characters (50% discount)

    Typical costs for 1000 documents/day:
    • Average 500 chars/doc → 500,000 chars/day → $12.50/month

    Compare to AWS: $1-2/month base + compute time

    GCP is more expensive for high-volume usage but simpler (no cold starts!)
  EOT
}

output "python_example_file" {
  description = "Path to Python usage example"
  value       = "${path.module}/python_usage_example.py"
}

output "config_file" {
  description = "Path to embedding configuration file"
  value       = "${path.module}/embedding_model_config.json"
}
