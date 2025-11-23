# Example Python code for using Vertex AI Text Embeddings
# This uses the managed API - no endpoint deployment needed!

from vertexai.language_models import TextEmbeddingModel
import vertexai

# Initialize Vertex AI
vertexai.init(
    project="gen-lang-client-0259050339",
    location="us-central1"
)

# Load the embedding model
model = TextEmbeddingModel.from_pretrained("text-embedding-004")

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
