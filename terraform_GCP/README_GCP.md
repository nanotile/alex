# Alex on Google Cloud Platform (GCP)

Multi-cloud deployment of Alex (Agentic Learning Equities eXplainer) on Google Cloud Platform.

## Overview

This directory contains Terraform configurations to deploy the Alex financial planning platform on GCP, mirroring the AWS deployment while leveraging GCP-native services.

## Architecture

Alex on GCP uses the following services:

| Component | AWS Service | GCP Service |
|-----------|-------------|-------------|
| **Compute** | Lambda | Cloud Run |
| **Database** | Aurora Serverless v2 | AlloyDB / Cloud SQL |
| **AI/ML** | Bedrock (Nova Pro) | Vertex AI (Gemini) |
| **Embeddings** | SageMaker | Vertex AI Embeddings |
| **Vector Storage** | S3 Vectors | Vertex AI Vector Search |
| **Container Registry** | ECR | Artifact Registry |
| **API Gateway** | API Gateway | API Gateway / Cloud Endpoints |
| **CDN** | CloudFront | Cloud CDN |
| **Message Queue** | SQS | Cloud Tasks |
| **Scheduler** | EventBridge | Cloud Scheduler |
| **Secrets** | Secrets Manager | Secret Manager |
| **Monitoring** | CloudWatch | Cloud Monitoring |

## Prerequisites

### 1. GCP Account & Project
- GCP account with billing enabled
- GCP project created
- Project ID noted

### 2. Tools Installed
```bash
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Terraform
# Already installed (used for AWS deployment)

# Docker
# Already installed (for container builds)
```

### 3. Authentication
```bash
# Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### 4. Enable Billing
```bash
# Link billing account to project (via console or gcloud)
gcloud billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

## Directory Structure

```
terraform_GCP/
├── 0_foundation/          # GCP project setup, APIs, service accounts
├── 1_network/             # VPC configuration (if needed)
├── 2_embeddings/          # Vertex AI embedding endpoint
├── 3_ingestion/           # Ingest function + Vertex AI Vector Search
├── 4_researcher/          # Researcher agent on Cloud Run
├── 5_database/            # AlloyDB/Cloud SQL
├── 6_agents/              # 5 agent Cloud Run services + Cloud Tasks
├── 7_frontend/            # Cloud Storage + Cloud CDN
├── 8_monitoring/          # Cloud Monitoring dashboards
├── variables.tf           # Shared variables
├── providers.tf           # GCP provider config
└── .env.gcp.example       # Environment variables template
```

## Deployment Order

Deploy modules in this order (one at a time):

1. **0_foundation** - Enable APIs, create service accounts
2. **2_embeddings** - Deploy Vertex AI embeddings
3. **5_database** - Deploy database (critical path)
4. **3_ingestion** - Deploy ingestion + vector storage
5. **4_researcher** - Deploy researcher agent
6. **6_agents** - Deploy 5 agents + orchestration
7. **7_frontend** - Deploy frontend + API
8. **8_monitoring** - Set up monitoring

## Quick Start

### Step 1: Configure Environment

```bash
# Copy environment template
cp .env.gcp.example .env.gcp

# Edit with your values
nano .env.gcp

# Set GCP project ID
export GCP_PROJECT_ID="your-project-id"
```

### Step 2: Create terraform.tfvars

Each module needs a `terraform.tfvars` file. Copy from the example:

```bash
cd terraform_GCP/0_foundation
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

### Step 3: Deploy Foundation

```bash
cd terraform_GCP/0_foundation
terraform init
terraform plan
terraform apply
```

### Step 4: Deploy Remaining Modules

Follow the deployment order above, repeating init/plan/apply for each module.

## Cost Estimates

Monthly cost estimates for GCP deployment:

| Service | Estimated Cost |
|---------|---------------|
| AlloyDB (2 vCPU, 16GB) | $150-200 |
| Cloud Run (6 services) | $30-50 |
| Vertex AI (Gemini) | $50-100 |
| Vertex AI Embeddings | $20-40 |
| Vertex AI Vector Search | $100-200 |
| Cloud Storage | $5-10 |
| Cloud CDN | $10-20 |
| Cloud Tasks | $5-10 |
| Networking | $10-20 |
| **Total** | **$380-650/month** |

**Note:** GCP may be more expensive than AWS primarily due to Vertex AI Vector Search. Consider using AlloyDB + pgvector for cost optimization (~$50-80/month savings).

## Multi-Cloud Strategy

### Running Both AWS and GCP

- **AWS**: Production (`alex.yourdomain.com`)
- **GCP**: Parallel/testing (`gcp.alex.yourdomain.com`)

### Data Synchronization

- **Clerk users**: Centralized authentication (works across both)
- **Database**: Scheduled export from AWS → GCP or bi-directional sync
- **Vectors**: Replicate ingested documents to both platforms

## Key Differences from AWS

### 1. Database Access
**AWS**: Aurora Data API (HTTP-based, no VPC needed)
**GCP**: Cloud SQL Python Connector (library-based connection)

All Cloud Run services use the connector library instead of HTTP API.

### 2. Vector Storage
**AWS**: S3 Vectors (AWS-native, low cost)
**GCP**: Vertex AI Vector Search (managed, higher cost) or AlloyDB + pgvector

### 3. LLM Models
**AWS**: Bedrock Nova Pro (`us.amazon.nova-pro-v1:0`)
**GCP**: Vertex AI Gemini (`gemini-1.5-pro`)

Different models may require prompt tuning for equivalent results.

### 4. Message Queue
**AWS**: SQS (pull-based with Lambda triggers)
**GCP**: Cloud Tasks (push-based HTTP targets)

## Troubleshooting

### Common Issues

**1. API Not Enabled**
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable aiplatform.googleapis.com
# ... (see 0_foundation/main.tf for full list)
```

**2. Permission Denied**
```bash
# Grant necessary IAM roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

**3. Terraform State Issues**
```bash
# Reset state if needed (careful!)
rm -rf .terraform terraform.tfstate*
terraform init
```

## Cleanup

To destroy GCP resources (in reverse order):

```bash
cd terraform_GCP/8_monitoring && terraform destroy
cd ../7_frontend && terraform destroy
cd ../6_agents && terraform destroy
cd ../5_database && terraform destroy  # Biggest cost savings
cd ../4_researcher && terraform destroy
cd ../3_ingestion && terraform destroy
cd ../2_embeddings && terraform destroy
cd ../0_foundation && terraform destroy
```

**Warning:** Destroying the database will delete all data. Export first if needed!

## Support

- **Documentation**: See individual module READMEs
- **AWS Comparison**: See `../terraform/` for AWS equivalents
- **Issues**: Check GCP quotas, API enablement, IAM permissions

## Next Steps

1. Deploy 0_foundation module
2. Verify APIs and service accounts
3. Proceed to 2_embeddings
4. Follow guides in order

For detailed instructions, see each module's README.md.
