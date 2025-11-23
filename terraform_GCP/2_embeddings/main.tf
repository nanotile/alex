terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.12"
    }
  }

  # Using local backend - state will be stored in terraform.tfstate in this directory
  # This is automatically gitignored for security
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# Data source for project information
data "google_project" "current" {}

# Service account for Vertex AI operations (if needed for custom deployments)
# Note: For managed Vertex AI endpoints, the Cloud Run SA will have sufficient permissions
# This is here for reference if you need custom model deployments

# Vertex AI Text Embeddings API is available as a managed service
# No endpoint deployment needed - it's pay-per-use API

# Create a sample configuration file to document the embedding model being used
resource "local_file" "embedding_config" {
  filename = "${path.module}/embedding_model_config.json"
  content = jsonencode({
    model_name = var.embedding_model_name
    task_type  = "RETRIEVAL_DOCUMENT"
    dimensions = 768  # text-embedding-004 produces 768-dimensional vectors
    api_endpoint = "https://${var.gcp_region}-aiplatform.googleapis.com"
    project_id = var.gcp_project
    location = var.gcp_region
    usage_note = "Use Vertex AI Text Embeddings API directly via client libraries"
    pricing = {
      note = "Pay per 1000 characters processed"
      documentation = "https://cloud.google.com/vertex-ai/pricing#text-embeddings"
    }
  })
}

# Output the model configuration
resource "local_file" "python_config_example" {
  filename = "${path.module}/python_usage_example.py"
  content = <<-EOT
# Example Python code for using Vertex AI Text Embeddings
# This uses the managed API - no endpoint deployment needed!

from vertexai.language_models import TextEmbeddingModel
import vertexai

# Initialize Vertex AI
vertexai.init(
    project="${var.gcp_project}",
    location="${var.gcp_region}"
)

# Load the embedding model
model = TextEmbeddingModel.from_pretrained("${var.embedding_model_name}")

# Generate embeddings
def get_embeddings(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"):
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed
        task_type: One of:
            - RETRIEVAL_DOCUMENT (for documents to be stored)
            - RETRIEVAL_QUERY (for search queries)
            - SEMANTIC_SIMILARITY
            - CLASSIFICATION
            - CLUSTERING

    Returns:
        List of embedding vectors
    """
    embeddings = model.get_embeddings(
        texts,
        task_type=task_type
    )

    return [embedding.values for embedding in embeddings]

# Example usage
if __name__ == "__main__":
    # Single text embedding
    texts = ["This is a test document about financial markets."]
    embeddings = get_embeddings(texts)

    print(f"Generated embedding with {len(embeddings[0])} dimensions")
    print(f"First 5 values: {embeddings[0][:5]}")
EOT
}
