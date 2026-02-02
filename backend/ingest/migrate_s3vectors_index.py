"""
Migrate S3 Vectors index from 384 dimensions (SageMaker) to 1536 dimensions (Bedrock Titan).

This script:
1. Deletes the existing 'financial-research' index (384 dimensions)
2. Creates a new index with 1536 dimensions for Bedrock Titan Embeddings v2

WARNING: This will delete all existing vectors! Run this only when migrating to Bedrock.
"""

import os
import boto3
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

# Get configuration
VECTOR_BUCKET = os.getenv('VECTOR_BUCKET')
INDEX_NAME = 'financial-research'
NEW_DIMENSION = 1024  # Bedrock Titan Embeddings v2 default dimension

if not VECTOR_BUCKET:
    print("Error: VECTOR_BUCKET not found in .env")
    print("Please ensure you have run Guide 3 and saved VECTOR_BUCKET to .env")
    exit(1)

# Initialize S3 Vectors client
s3_vectors = boto3.client('s3vectors')


def list_indexes():
    """List all indexes in the vector bucket."""
    try:
        response = s3_vectors.list_indexes(
            vectorBucketName=VECTOR_BUCKET
        )
        return response.get('indexes', [])
    except Exception as e:
        print(f"Error listing indexes: {e}")
        return []


def delete_index(index_name):
    """Delete an existing index."""
    try:
        print(f"Deleting index '{index_name}'...")
        s3_vectors.delete_index(
            vectorBucketName=VECTOR_BUCKET,
            indexName=index_name
        )
        print(f"  Index '{index_name}' deleted successfully")
        return True
    except s3_vectors.exceptions.NotFoundException:
        print(f"  Index '{index_name}' does not exist (nothing to delete)")
        return True
    except Exception as e:
        print(f"  Error deleting index: {e}")
        return False


def create_index(index_name, dimension):
    """Create a new index with specified dimension."""
    try:
        print(f"Creating index '{index_name}' with {dimension} dimensions...")
        s3_vectors.create_index(
            vectorBucketName=VECTOR_BUCKET,
            indexName=index_name,
            dimension=dimension,
            distanceMetric='cosine',
            dataType='float32'
        )
        print(f"  Index '{index_name}' created successfully")
        return True
    except s3_vectors.exceptions.ConflictException:
        print(f"  Index '{index_name}' already exists")
        return False
    except Exception as e:
        print(f"  Error creating index: {e}")
        return False


def main():
    """Migrate the S3 Vectors index to 1536 dimensions."""
    print("=" * 60)
    print("S3 Vectors Index Migration")
    print("From: 384 dimensions (SageMaker HuggingFace)")
    print("To:   1024 dimensions (Bedrock Titan Embeddings v2)")
    print("=" * 60)
    print()
    print(f"Bucket: {VECTOR_BUCKET}")
    print(f"Index:  {INDEX_NAME}")
    print()

    # List current indexes
    print("Current indexes:")
    indexes = list_indexes()
    if indexes:
        for idx in indexes:
            print(f"  - {idx.get('indexName', 'unknown')} (dimension: {idx.get('dimension', '?')})")
    else:
        print("  (no indexes found)")
    print()

    # Confirm before proceeding
    print("WARNING: This will DELETE all existing vectors in the index!")
    print("         You will need to re-ingest your documents after migration.")
    print()
    response = input("Continue with migration? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return

    print()

    # Step 1: Delete existing index
    if not delete_index(INDEX_NAME):
        print("Migration failed: Could not delete existing index")
        return

    # Step 2: Create new index with 1536 dimensions
    if not create_index(INDEX_NAME, NEW_DIMENSION):
        print("Migration failed: Could not create new index")
        return

    print()
    print("=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Ensure Bedrock Titan Embeddings access is enabled in AWS Console")
    print("  2. Re-ingest your documents:")
    print("     cd backend/ingest && uv run test_ingest_s3vectors.py")
    print("  3. Test search functionality:")
    print("     cd backend/ingest && uv run test_search_s3vectors.py")


if __name__ == "__main__":
    main()
