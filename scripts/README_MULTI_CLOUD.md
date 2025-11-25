# Multi-Cloud Deployment Tools for Alex Project

Unified deployment and management scripts for deploying Alex to AWS, GCP, or both clouds simultaneously.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Script](#deployment-script)
- [Destroy Script](#destroy-script)
- [Available Modules](#available-modules)
- [Cost Management](#cost-management)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Overview

The Alex project can be deployed to **AWS**, **GCP**, or **both clouds** using these unified scripts:

- **`deploy_multi_cloud.py`** - Deploy infrastructure
- **`destroy_multi_cloud.py`** - Destroy infrastructure (with cost savings!)

### Key Features

✅ **Multi-cloud support** - Deploy to AWS, GCP, or both
✅ **Dependency resolution** - Automatically deploys in correct order
✅ **Cost estimation** - Preview costs before deploying
✅ **Health checks** - Verify services after deployment
✅ **Dry-run mode** - Preview without executing
✅ **Module selection** - Deploy only what you need
✅ **Colored output** - Easy-to-read progress indicators
✅ **Rollback support** - Stops on first error

---

## Prerequisites

### Required Tools

1. **Terraform** (v1.0+)
   ```bash
   terraform --version
   ```

2. **AWS CLI** (configured)
   ```bash
   aws configure
   aws sts get-caller-identity
   ```

3. **Google Cloud SDK** (configured)
   ```bash
   gcloud --version
   gcloud auth list
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **UV** (Python package manager)
   ```bash
   uv --version
   ```

### Configuration Files

Each terraform directory needs a `terraform.tfvars` file:

```bash
# Copy examples and configure
cp terraform/5_database/terraform.tfvars.example terraform/5_database/terraform.tfvars
# Edit with your values
```

**Required for each module you want to deploy!**

---

## Quick Start

### Deploy Database to GCP

```bash
cd scripts
uv run deploy_multi_cloud.py --cloud gcp --modules database
```

### Deploy Everything to AWS

```bash
cd scripts
uv run deploy_multi_cloud.py --cloud aws --modules all
```

### Deploy Database + Agents to Both Clouds

```bash
cd scripts
uv run deploy_multi_cloud.py --cloud both --modules database,agents
```

### Preview (Dry Run)

```bash
cd scripts
uv run deploy_multi_cloud.py --cloud both --modules all --dry-run
```

---

## Deployment Script

### Usage

```bash
uv run deploy_multi_cloud.py --cloud {aws|gcp|both} --modules {modules} [options]
```

### Options

| Flag | Description | Example |
|------|-------------|---------|
| `--cloud` | Target cloud (required) | `aws`, `gcp`, `both` |
| `--modules` | Modules to deploy (required) | `all`, `database`, `database,agents` |
| `--dry-run` | Preview without executing | |
| `--skip-checks` | Skip health checks (faster) | |

### Examples

```bash
# Deploy database only to GCP
uv run deploy_multi_cloud.py --cloud gcp --modules database

# Deploy frontend to AWS (requires agents to exist first)
uv run deploy_multi_cloud.py --cloud aws --modules frontend

# Deploy everything to both clouds
uv run deploy_multi_cloud.py --cloud both --modules all

# Preview deployment without executing
uv run deploy_multi_cloud.py --cloud aws --modules all --dry-run

# Deploy specific modules
uv run deploy_multi_cloud.py --cloud gcp --modules foundation,embeddings,database
```

### What Happens During Deployment

1. **Validation** - Checks terraform.tfvars exist
2. **Dependency Resolution** - Orders modules correctly
3. **Cost Estimation** - Shows projected monthly costs
4. **Confirmation** - Asks for approval (unless dry-run)
5. **Terraform Init** - Initializes providers
6. **Terraform Apply** - Deploys infrastructure
7. **Health Checks** - Verifies services are running
8. **Output Display** - Shows endpoints and URLs

### Example Output

```
🚀 Multi-Cloud Deployment Tool for Alex
========================================

Configuration:
  Cloud: both
  Modules: database, agents
  Dry Run: No

📋 Deployment Order:
  1. GCP: GCP Foundation
  2. GCP: Cloud SQL Database
  3. AWS: IAM Permissions
  4. AWS: Aurora Database
  5. GCP: Tagger Agent (Cloud Run)
  6. AWS: AI Agents (5 Lambdas)

💰 Estimated Monthly Cost:
  AWS: $66.00
  GCP: $37.00
  Total: $103.00/month

Continue? [y/N]: y

ℹ️  [1/6] GCP GCP Foundation (terraform_GCP/0_foundation)
   terraform init... done
   terraform apply... done
   Health check... (skipped)
   Duration: 1m 23s

✅ [2/6] GCP Cloud SQL Database (terraform_GCP/5_database)
   terraform init... done
   terraform apply... done
   Health check... ✅ Healthy
   Duration: 4m 12s

... (continues)

✅ 🎉 Deployment Complete! (Total: 18m 45s)

Deployment Outputs

AWS Endpoints:
  database.cluster_endpoint: aurora-cluster-xxx.us-east-1.rds.amazonaws.com
  agents.planner_function_name: alex-planner

GCP Endpoints:
  database.instance_connection_name: project:region:instance
  agents.service_url: https://tagger-agent-xxx.run.app

Next Steps:
  - Update frontend/.env.production.local with API_URL
  - Test endpoints with curl or browser
  - Monitor costs in AWS/GCP consoles
```

---

## Destroy Script

### Usage

```bash
uv run destroy_multi_cloud.py --cloud {aws|gcp|both} --modules {modules} [options]
```

### Options

| Flag | Description | Example |
|------|-------------|---------|
| `--cloud` | Target cloud (required) | `aws`, `gcp`, `both` |
| `--modules` | Modules to destroy (required) | `all`, `database`, `database,agents` |
| `--dry-run` | Preview without executing | |

### Examples

```bash
# Destroy database on GCP to save $30/month
uv run destroy_multi_cloud.py --cloud gcp --modules database

# Destroy expensive AWS services (researcher + database)
uv run destroy_multi_cloud.py --cloud aws --modules researcher,database

# Destroy everything on both clouds
uv run destroy_multi_cloud.py --cloud both --modules all

# Preview destruction
uv run destroy_multi_cloud.py --cloud aws --modules all --dry-run
```

### Safety Features

- **Reverse order destruction** - Destroys in reverse dependency order
- **Confirmation required** - Must type `destroy` to confirm
- **Cost savings displayed** - Shows how much you'll save
- **Dry-run mode** - Preview without executing
- **Skip missing resources** - Doesn't fail if already destroyed

### Example Output

```
🗑️  Multi-Cloud Destroy Tool for Alex
====================================

Configuration:
  Cloud: aws
  Modules: researcher, database
  Dry Run: No

📋 Destruction Order:
  1. AWS: Research Agent
  2. AWS: Aurora Database

💰 Monthly Cost Savings:
  AWS: $116.00
  Total: $116.00/month

⚠️  WARNING: This will PERMANENTLY DELETE the selected infrastructure!
Type 'destroy' to confirm: destroy

ℹ️  [1/2] AWS Research Agent (terraform/4_researcher)
   terraform init... done
   terraform destroy... done
   Duration: 2m 18s

✅ [2/2] AWS Aurora Database (terraform/5_database)
   terraform init... done
   terraform destroy... done
   Duration: 5m 44s

✅ Destruction Complete! (Total: 8m 2s)

Resources Destroyed:
  - AWS: Research Agent
  - AWS: Aurora Database

💰 You will save ~$116.00/month
```

---

## Available Modules

### AWS Modules

| Module | Description | Directory | Dependencies | Cost/Month |
|--------|-------------|-----------|--------------|------------|
| `foundation` | IAM permissions | `terraform/1_permissions` | None | $0 |
| `embeddings` | SageMaker endpoint | `terraform/2_sagemaker` | foundation | $10 |
| `ingestion` | S3 Vectors + Lambda | `terraform/3_ingestion` | embeddings | $1 |
| `researcher` | App Runner research agent | `terraform/4_researcher` | ingestion | $51 |
| `database` | Aurora Serverless v2 | `terraform/5_database` | foundation | $65 |
| `agents` | 5 Lambda agents + SQS | `terraform/6_agents` | database | $1 |
| `frontend` | S3 + CloudFront + API | `terraform/7_frontend` | agents | $2 |
| `monitoring` | CloudWatch dashboards | `terraform/8_enterprise` | frontend | $6 |

**Total AWS Cost**: ~$136/month

### GCP Modules

| Module | Description | Directory | Dependencies | Cost/Month |
|--------|-------------|-----------|--------------|------------|
| `foundation` | APIs + Artifact Registry | `terraform_GCP/0_foundation` | None | $0 |
| `embeddings` | Vertex AI configuration | `terraform_GCP/2_embeddings` | foundation | $3 |
| `database` | Cloud SQL PostgreSQL | `terraform_GCP/5_database` | foundation | $30 |
| `agents` | Cloud Run Tagger agent | `terraform_GCP/6_agents` | database | $7 |

**Total GCP Cost**: ~$40/month (only partial deployment)

---

## Cost Management

### Monthly Cost Breakdown

**AWS (Full Deployment)**:
- 💰 Aurora Serverless v2: **$65** (highest cost!)
- 💰 App Runner (Researcher): **$51** (second highest)
- SageMaker: $10
- CloudWatch: $6
- Frontend: $2
- Agents: $1
- Ingestion: $1
- **Total: ~$136/month**

**GCP (Partial Deployment)**:
- 💰 Cloud SQL: **$30** (highest cost)
- Cloud Run Tagger: $7
- Vertex AI: $3 (usage-based)
- **Total: ~$40/month**

### Cost-Saving Strategies

#### Save $116/month (AWS)
```bash
# Destroy expensive services when not in use
uv run destroy_multi_cloud.py --cloud aws --modules researcher,database
```

#### Save $30/month (GCP)
```bash
# Destroy GCP database when not in use
uv run destroy_multi_cloud.py --cloud gcp --modules database
```

#### Weekend Shutdown
```bash
# Friday evening
uv run destroy_multi_cloud.py --cloud both --modules researcher,database

# Monday morning
uv run deploy_multi_cloud.py --cloud both --modules researcher,database
```

#### Development vs Production
```bash
# Development: Use GCP (cheaper)
uv run deploy_multi_cloud.py --cloud gcp --modules database,agents

# Production: Use AWS (more services)
uv run deploy_multi_cloud.py --cloud aws --modules all
```

---

## Troubleshooting

### Issue: "terraform.tfvars not found"

**Solution**: Copy example file and configure it

```bash
cd terraform/5_database
cp terraform.tfvars.example terraform.tfvars
# Edit with your values
vim terraform.tfvars
```

### Issue: "Dependency resolution failed"

**Solution**: Deploy dependencies first

```bash
# Instead of deploying agents directly, deploy database first
uv run deploy_multi_cloud.py --cloud gcp --modules database
# Then deploy agents
uv run deploy_multi_cloud.py --cloud gcp --modules agents

# Or deploy both (script handles order)
uv run deploy_multi_cloud.py --cloud gcp --modules database,agents
```

### Issue: "Health check failed"

**Solution**: Use `--skip-checks` to bypass (non-critical)

```bash
uv run deploy_multi_cloud.py --cloud gcp --modules agents --skip-checks
```

### Issue: "AWS credentials not configured"

**Solution**: Configure AWS CLI

```bash
aws configure
# Enter your Access Key ID, Secret Access Key, and region
```

### Issue: "GCP project not set"

**Solution**: Set default project

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
```

### Issue: "Deployment stuck/timeout"

**Cause**: Large resources (databases) can take 10+ minutes

**Solution**: Be patient or check AWS/GCP console for progress

```bash
# For AWS Aurora
aws rds describe-db-clusters --query "DBClusters[*].[DBClusterIdentifier,Status]"

# For GCP Cloud SQL
gcloud sql instances list
```

---

## Advanced Usage

### Deploy Only Missing Modules

```bash
# Check what's already deployed
terraform -chdir=terraform/5_database state list
terraform -chdir=terraform_GCP/5_database state list

# Deploy only what's missing
uv run deploy_multi_cloud.py --cloud gcp --modules agents
```

### Parallel Cloud Deployment

The script automatically handles parallel-safe operations:

```bash
# Deploys AWS and GCP databases in parallel (independent)
uv run deploy_multi_cloud.py --cloud both --modules database
```

### Custom Module Order

The script automatically resolves dependencies, but you can deploy in stages:

```bash
# Stage 1: Foundation
uv run deploy_multi_cloud.py --cloud both --modules foundation

# Stage 2: Data layer
uv run deploy_multi_cloud.py --cloud both --modules embeddings,database

# Stage 3: Compute layer
uv run deploy_multi_cloud.py --cloud both --modules agents

# Stage 4: Frontend
uv run deploy_multi_cloud.py --cloud aws --modules frontend
```

### Integration with Existing Scripts

These scripts complement existing deployment tools:

```bash
# Use existing script for frontend assets
cd scripts
uv run deploy.py

# Use multi-cloud tool for infrastructure
uv run deploy_multi_cloud.py --cloud aws --modules agents
```

---

## Architecture Comparison

### AWS Architecture

```
User → CloudFront → S3 (Frontend)
                 ↓
            API Gateway → Lambda (FastAPI)
                 ↓
        ┌────────┴────────┐
        ↓                 ↓
    Aurora DB         SQS Queue
                         ↓
            ┌────────────┼────────────┐
            ↓            ↓            ↓
        Planner      Tagger      Reporter
        (Lambda)    (Lambda)    (Lambda)
                         ↓
                    ┌────┴────┐
                    ↓         ↓
                Charter   Retirement
                (Lambda)  (Lambda)
```

### GCP Architecture (Current)

```
User → Cloud Run (Tagger)
          ↓
    Cloud SQL (PostgreSQL)
```

### Multi-Cloud Hybrid

```
User → CloudFront (AWS) → S3 Frontend
              ↓
         API Gateway (AWS)
              ↓
         Lambda (FastAPI)
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
Aurora (AWS)      Cloud SQL (GCP)
    ↓                   ↓
Lambda Agents     Cloud Run Agent
```

---

## Next Steps

After deploying infrastructure:

1. **Update frontend configuration**
   ```bash
   # Edit frontend/.env.production.local
   NEXT_PUBLIC_API_URL=https://your-api-url.com
   ```

2. **Test endpoints**
   ```bash
   # AWS
   curl https://your-api-gateway-url.com/health

   # GCP
   curl https://tagger-agent-xxx.run.app/health
   ```

3. **Deploy frontend** (AWS only currently)
   ```bash
   cd scripts
   uv run deploy.py
   ```

4. **Monitor costs**
   - AWS: https://console.aws.amazon.com/billing/
   - GCP: https://console.cloud.google.com/billing

5. **Set up monitoring**
   ```bash
   uv run deploy_multi_cloud.py --cloud aws --modules monitoring
   ```

---

## Contributing

To add new modules:

1. Add module definition to `deploy_multi_cloud.py`:
   ```python
   GCP_MODULES["new_module"] = Module(
       name="new_module",
       display_name="New Service",
       cloud=Cloud.GCP,
       terraform_dir="terraform_GCP/X_new",
       dependencies=["foundation"],
       estimated_monthly_cost=15.0,
   )
   ```

2. Add health check function (optional):
   ```python
   def health_check_new_module(self, module: Module) -> bool:
       # Your health check logic
       return True
   ```

3. Map to health checks dict:
   ```python
   health_checks = {
       ("GCP", "new_module"): self.health_check_new_module,
   }
   ```

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review AWS/GCP console for resource status
3. Check terraform state: `terraform state list`
4. Review logs: `terraform show`

---

**Happy Deploying! 🚀**
