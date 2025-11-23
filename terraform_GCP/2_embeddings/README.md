# Module 2: Embeddings

## Overview

This module configures Vertex AI Text Embeddings for the Alex project on GCP. Unlike AWS SageMaker which requires endpoint deployment, **GCP Vertex AI provides embeddings as a fully managed API** - no deployment needed!

## Key Differences from AWS

| Aspect | AWS SageMaker | GCP Vertex AI |
|--------|---------------|---------------|
| **Setup** | Deploy endpoint (5-10 min) | Use API immediately |
| **Model** | all-MiniLM-L6-v2 (384 dims) | text-embedding-004 (768 dims) |
| **Cold Starts** | 5-60 seconds | None (always available) |
| **Pricing** | Base cost + compute time | Pay-per-character only |
| **Scaling** | Auto-scaling (serverless) | Fully managed by Google |
| **Typical Cost** | $1-2/month (low usage) | $12-25/month (1000 docs/day) |

## What This Module Creates

This module **does NOT create infrastructure resources** - it only:
1. Creates documentation files explaining how to use Vertex AI embeddings
2. Generates Python code examples
3. Outputs configuration for your `.env.gcp` file

**Why no infrastructure?**
- Vertex AI Text Embeddings is a managed API service
- No endpoint deployment needed
- Access is controlled by IAM (already set up in Module 0)
- You pay only for actual API usage

## Prerequisites

- Module 0 (Foundation) deployed successfully
- Service account `alex-gcl-cloudrun-sa` has Vertex AI User role
- Vertex AI API enabled (done in Module 0)

## Deployment Steps

### Step 1: Configure Variables

```bash
cd terraform_GCP/2_embeddings

# Copy example to actual config
cp terraform.tfvars.example terraform.tfvars

# Edit with your values (should match Module 0)
nano terraform.tfvars
```

Required values:
```hcl
gcp_project = "gen-lang-client-0259050339"  # Your project ID
gcp_region = "us-central1"                   # Your region
project_name = "alex-gcl"                    # Your project name
```

### Step 2: Deploy (Generate Config)

```bash
terraform init
terraform plan
terraform apply
```

This creates local documentation files only - no GCP resources deployed!

### Step 3: Review Generated Files

After applying, you'll have:

1. **embedding_model_config.json** - Configuration details
2. **python_usage_example.py** - Working Python code

### Step 4: Update Environment Variables

Add to your `.env.gcp` file (in project root):

```bash
# Module 2: Embeddings
GCP_PROJECT=gen-lang-client-0259050339
GCP_REGION=us-central1
VERTEX_EMBEDDING_MODEL=text-embedding-004
```

### Step 5: Install Required Library

```bash
# Navigate to your backend directory
cd ../../backend

# Add Vertex AI library to your uv project
uv add google-cloud-aiplatform
```

### Step 6: Test the Embeddings API

Create a test file to verify everything works:

```bash
cd backend
```

Create `test_vertex_embeddings.py`:
```python
import vertexai
from vertexai.language_models import TextEmbeddingModel
import os

# Initialize Vertex AI
project_id = os.getenv("GCP_PROJECT", "gen-lang-client-0259050339")
region = os.getenv("GCP_REGION", "us-central1")

vertexai.init(project=project_id, location=region)

# Load the model
model = TextEmbeddingModel.from_pretrained("text-embedding-004")

# Test embedding generation
test_text = "This is a test of Vertex AI embeddings for Alex."

embeddings = model.get_embeddings(
    [test_text],
    task_type="RETRIEVAL_DOCUMENT"
)

print(f"✅ Success!")
print(f"Generated embedding with {len(embeddings[0].values)} dimensions")
print(f"First 10 values: {embeddings[0].values[:10]}")
```

Run the test:
```bash
uv run test_vertex_embeddings.py
```

Expected output:
```
✅ Success!
Generated embedding with 768 dimensions
First 10 values: [0.0123, -0.0456, 0.0789, ...]
```

## Understanding Task Types

Vertex AI embeddings support different task types for optimization:

```python
# For documents you're storing/indexing
embeddings = model.get_embeddings(
    texts,
    task_type="RETRIEVAL_DOCUMENT"
)

# For search queries
embeddings = model.get_embeddings(
    texts,
    task_type="RETRIEVAL_QUERY"
)

# For comparing similarity
embeddings = model.get_embeddings(
    texts,
    task_type="SEMANTIC_SIMILARITY"
)

# For classification tasks
embeddings = model.get_embeddings(
    texts,
    task_type="CLASSIFICATION"
)

# For clustering
embeddings = model.get_embeddings(
    texts,
    task_type="CLUSTERING"
)
```

**Best practice for Alex:**
- Use `RETRIEVAL_DOCUMENT` when embedding financial documents
- Use `RETRIEVAL_QUERY` when embedding user questions

## Cost Analysis

### Pricing Structure

- **$0.025 per 1,000 characters** (first 1 million chars/month)
- **$0.0125 per 1,000 characters** (above 1 million chars/month)

### Cost Examples

**Low Usage (100 docs/day):**
- 100 docs × 500 chars/doc = 50,000 chars/day
- 1.5 million chars/month
- First 1M: $25
- Next 0.5M: $6.25
- **Total: ~$31/month**

**Medium Usage (1000 docs/day):**
- 1000 docs × 500 chars/doc = 500,000 chars/day
- 15 million chars/month
- First 1M: $25
- Next 14M: $175
- **Total: ~$200/month**

**Compare to AWS:**
- AWS SageMaker Serverless: $1-2/month base + per-request compute
- For low volume, AWS is cheaper
- For high volume with many short requests, GCP may be comparable

### Cost Optimization Tips

1. **Batch requests** - Process multiple texts in one API call
2. **Cache embeddings** - Store results in database/Cloud Storage
3. **Deduplicate** - Don't re-embed identical text
4. **Monitor usage** - Check Cloud Billing reports

## Outputs

Run `terraform output` to see:

```bash
terraform output
```

Key outputs:
- `embedding_model_name` - Model being used (text-embedding-004)
- `vertex_ai_location` - Region for API calls (us-central1)
- `vertex_ai_endpoint` - Full API endpoint URL
- `embedding_dimensions` - Vector dimensions (768)
- `python_example_file` - Path to usage example
- `setup_instructions` - Detailed usage guide

## Migrating from AWS

If you're migrating existing embeddings from AWS:

**⚠️ IMPORTANT: Vector dimensions are different!**
- AWS (all-MiniLM-L6-v2): 384 dimensions
- GCP (text-embedding-004): 768 dimensions

**This means:**
- You CANNOT mix AWS and GCP embeddings in the same vector search
- You must re-embed all documents when migrating
- You'll need separate vector indices for AWS and GCP

**Migration strategy:**
1. Keep AWS embeddings in S3 Vectors
2. Create new GCP embeddings in Vertex AI Vector Search
3. Run both systems in parallel
4. Gradually migrate users to GCP
5. Eventually deprecate AWS infrastructure

## Troubleshooting

### Error: "Permission denied"

Check that your service account has the Vertex AI User role:

```bash
gcloud projects get-iam-policy gen-lang-client-0259050339 \
  --flatten="bindings[].members" \
  --filter="bindings.members:alex-gcl-cloudrun-sa@"
```

Should include: `roles/aiplatform.user`

### Error: "Model not found"

Ensure the model is available in your region:

```bash
# List available models
gcloud ai models list --region=us-central1
```

If `text-embedding-004` is not available, try `text-embedding-005` or use a different region.

### Error: "Quota exceeded"

Check your Vertex AI quotas:

```bash
gcloud services quota list \
  --service=aiplatform.googleapis.com \
  --filter="metric.type:aiplatform.googleapis.com/predict_requests"
```

Request quota increase if needed: https://console.cloud.google.com/iam-admin/quotas

### High Costs

If costs are higher than expected:

1. **Check usage**:
   ```bash
   # View Vertex AI usage in Cloud Console
   # Navigation: Vertex AI → Dashboard → Usage
   ```

2. **Enable detailed logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

3. **Review batch sizes** - Larger batches = fewer API calls

4. **Check for duplicate processing** - Add caching layer

## Next Steps

1. ✅ Embeddings API configured
2. ✅ Python examples generated
3. ✅ Test script verified
4. ➡️ Deploy Module 5: Database (AlloyDB/Cloud SQL)
5. Deploy Module 3: Ingestion & Vector Storage

**Note:** We'll deploy the database (Module 5) before ingestion (Module 3) because the ingestion function needs database access.

See the main `terraform_GCP/README_GCP.md` for the complete deployment order.

## Cleanup

To remove the local files created by this module:

```bash
terraform destroy
```

This only removes the local documentation files - no GCP resources to clean up!

## Additional Resources

- [Vertex AI Text Embeddings Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-text-embeddings)
- [Pricing Details](https://cloud.google.com/vertex-ai/pricing#text-embeddings)
- [Python Client Library](https://cloud.google.com/python/docs/reference/aiplatform/latest)
- [Best Practices for Embeddings](https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/best-practices)
