# Quick Start Guide - Multi-Cloud Deployment

## TL;DR - Common Commands

### Deploy

```bash
cd scripts

# Deploy GCP database and agents
uv run deploy_multi_cloud.py --cloud gcp --modules database,agents

# Deploy AWS database only
uv run deploy_multi_cloud.py --cloud aws --modules database

# Deploy to both clouds
uv run deploy_multi_cloud.py --cloud both --modules database,agents

# Preview without executing
uv run deploy_multi_cloud.py --cloud both --modules all --dry-run
```

### Destroy (Save Money!)

```bash
cd scripts

# Destroy GCP database ($30/month savings)
uv run destroy_multi_cloud.py --cloud gcp --modules database

# Destroy AWS expensive services ($116/month savings)
uv run destroy_multi_cloud.py --cloud aws --modules researcher,database

# Preview destruction
uv run destroy_multi_cloud.py --cloud both --modules all --dry-run
```

---

## What's Currently Deployed

### GCP (Currently Active)
- ✅ Cloud SQL Database ($30/mo)
- ✅ Tagger Agent on Cloud Run ($7/mo)
- **Total: $37/month**

### AWS (Based on terraform state)
Check with:
```bash
# See what's deployed
cd terraform/5_database && terraform state list
cd terraform/6_agents && terraform state list
```

---

## Common Workflows

### Weekend Cost Savings
```bash
# Friday: Shutdown expensive services
cd scripts
uv run destroy_multi_cloud.py --cloud gcp --modules database

# Monday: Restart
uv run deploy_multi_cloud.py --cloud gcp --modules database
```

### Add New Service to GCP
```bash
# Deploy database first (if not already deployed)
uv run deploy_multi_cloud.py --cloud gcp --modules database

# Then deploy agents
uv run deploy_multi_cloud.py --cloud gcp --modules agents
```

### Multi-Cloud Development
```bash
# Use GCP for development (cheaper)
uv run deploy_multi_cloud.py --cloud gcp --modules database,agents

# Use AWS for production (full features)
uv run deploy_multi_cloud.py --cloud aws --modules all
```

---

## Available Modules

| Module | AWS | GCP | Cost (AWS) | Cost (GCP) |
|--------|-----|-----|------------|------------|
| `embeddings` | ✅ | ✅ | $10/mo | $3/mo |
| `ingestion` | ✅ | ❌ | $1/mo | - |
| `researcher` | ✅ | ❌ | $51/mo | - |
| `database` | ✅ | ✅ | $65/mo | $30/mo |
| `agents` | ✅ | ✅ (partial) | $1/mo | $7/mo |
| `frontend` | ✅ | ❌ | $2/mo | - |
| `monitoring` | ✅ | ❌ | $6/mo | - |

---

## Troubleshooting

### "terraform.tfvars not found"
```bash
# Go to the module directory
cd terraform_GCP/5_database

# Copy example and edit
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # or vim, code, etc.
```

### Check What's Deployed
```bash
# For each module
terraform -chdir=terraform_GCP/5_database state list
terraform -chdir=terraform_GCP/6_agents state list
```

### See Current Costs
```bash
# AWS
aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-30 --granularity MONTHLY --metrics BlendedCost

# GCP
gcloud billing accounts list
gcloud billing projects describe PROJECT_ID
```

### Manual Deploy if Script Fails
```bash
cd terraform_GCP/5_database
terraform init
terraform plan
terraform apply
```

---

## Next Steps

1. **Configure terraform.tfvars** in each module you want to deploy
2. **Test with --dry-run** before actually deploying
3. **Monitor costs** regularly in AWS/GCP consoles
4. **Destroy when not in use** to save money

For full documentation, see `README_MULTI_CLOUD.md`
