# Module 0: Foundation

## Overview

This module sets up the foundational Google Cloud Platform infrastructure for the Alex project. It must be deployed **first** before any other modules.

## What This Module Creates

### 1. API Enablement
Enables all required Google Cloud APIs:
- Cloud Run (serverless containers)
- Cloud SQL / AlloyDB (database)
- Vertex AI (AI/ML models)
- Secret Manager (credentials)
- Cloud Storage (object storage)
- Cloud Tasks (message queue)
- Cloud Scheduler (cron jobs)
- Artifact Registry (container images)
- Cloud Monitoring & Logging

### 2. Service Accounts

**Cloud Run Service Account** (`alex-cloudrun-sa`)
- Used by all Cloud Run services (agents, API, researcher)
- Permissions:
  - Cloud SQL Client
  - Secret Manager Secret Accessor
  - Vertex AI User
  - Storage Object Admin
  - Cloud Tasks Enqueuer
  - Cloud Run Invoker (for agent-to-agent calls)
  - Logs Writer
  - Monitoring Metric Writer

**Cloud Scheduler Service Account** (`alex-scheduler-sa`)
- Used by Cloud Scheduler to trigger the researcher agent
- Permissions:
  - Cloud Run Invoker

### 3. Artifact Registry
- Docker repository for storing agent container images
- Location: Same as `gcp_region`
- Name: `alex-docker-repo`

## Prerequisites

### 1. GCP Project
Create a new GCP project or use an existing one:

```bash
# Create new project (optional)
gcloud projects create YOUR_PROJECT_ID --name="Alex GCP"

# Set as active project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Billing
Link a billing account to the project:

```bash
# List billing accounts
gcloud billing accounts list

# Link to project
gcloud billing projects link YOUR_PROJECT_ID \
  --billing-account=BILLING_ACCOUNT_ID
```

### 3. Authentication
Authenticate Terraform with GCP:

```bash
# Application default credentials
gcloud auth application-default login

# Or use a service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Deployment Steps

### Step 1: Configure Variables

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your GCP project ID
nano terraform.tfvars
```

Required values:
```hcl
gcp_project = "your-actual-project-id"
gcp_region  = "us-central1"  # Or your preferred region
```

### Step 2: Initialize Terraform

```bash
terraform init
```

This downloads the required providers (google, google-beta).

### Step 3: Review the Plan

```bash
terraform plan
```

Review the resources that will be created. You should see:
- 16 API enablements
- 2 service accounts
- 10 IAM member bindings
- 1 Artifact Registry repository

### Step 4: Apply

```bash
terraform apply
```

Type `yes` when prompted. This will take 5-10 minutes as APIs are enabled.

### Step 5: Verify

Check the outputs:

```bash
terraform output
```

You should see:
- Service account emails
- Artifact Registry repository URL
- Enabled APIs list

## Outputs

| Output | Description | Used By |
|--------|-------------|---------|
| `project_id` | GCP Project ID | All modules |
| `region` | GCP Region | All modules |
| `cloudrun_service_account_email` | Cloud Run SA email | Modules 2-7 |
| `scheduler_service_account_email` | Scheduler SA email | Module 4 |
| `artifact_registry_repository_url` | Docker repo URL | Modules 4, 6 |

## Post-Deployment

### 1. Save Outputs

Save the service account emails to your `.env.gcp` file:

```bash
# Get the Cloud Run service account email
terraform output cloudrun_service_account_email

# Add to .env.gcp
echo "CLOUDRUN_SERVICE_ACCOUNT=$(terraform output -raw cloudrun_service_account_email)" >> ../../.env.gcp
```

### 2. Configure Docker for Artifact Registry

```bash
# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev
```

Replace `us-central1` with your region if different.

### 3. Verify API Enablement

```bash
# List enabled APIs
gcloud services list --enabled
```

All APIs from `required_apis` should be listed.

## Cost

This module has **minimal cost**:
- Service accounts: **Free**
- IAM bindings: **Free**
- API enablement: **Free**
- Artifact Registry: **$0.10/GB** storage (starts free)

Estimated monthly cost: **$0-5** (depending on container image storage)

## Troubleshooting

### Error: "API not enabled"
Wait 2-3 minutes after `terraform apply` for APIs to fully activate, then retry the next module.

### Error: "Billing not enabled"
```bash
# Check billing status
gcloud beta billing projects describe YOUR_PROJECT_ID

# Enable billing via console
https://console.cloud.google.com/billing
```

### Error: "Permission denied"
Ensure your gcloud user has the following roles:
- Project Editor or Owner
- Service Account Admin
- Project IAM Admin

```bash
# Check your permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL"
```

### Error: "Quota exceeded"
Check project quotas:
```bash
gcloud compute project-info describe --project=YOUR_PROJECT_ID
```

Request quota increases if needed: https://console.cloud.google.com/iam-admin/quotas

## Cleanup

To destroy this module:

```bash
terraform destroy
```

**WARNING:** Destroy all other modules first (in reverse order) before destroying foundation, as they depend on the service accounts and APIs enabled here.

## Next Steps

1. ✅ Foundation deployed successfully
2. ➡️ Deploy Module 2: Embeddings (`../2_embeddings/`)
3. Deploy Module 5: Database (`../5_database/`)
4. Continue with remaining modules

See the main `terraform_GCP/README_GCP.md` for the complete deployment order.
