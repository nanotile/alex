# AWS Cost Management & Deployment Scripts

This directory contains Python scripts to manage AWS infrastructure costs and deployment status for the Alex project.

## Scripts Overview

### 1. `deployment_status.py` - Check Deployment Status ⭐ NEW

**Purpose:** Get comprehensive status of what's deployed and what's missing in your AWS infrastructure.

**Features:**
- ✅ Shows deployed vs not-deployed modules
- 💰 Calculates current and potential costs
- 📊 Resource counts and last modified dates
- 🔍 Optional AWS health checks
- 🎯 Identifies configuration issues (missing tfvars, uninitialized terraform)
- 💡 Smart recommendations based on deployment state
- 📋 JSON output for automation

**Usage:**

```bash
# Full status report
uv run scripts/AWS_START_STOP/deployment_status.py

# Quick summary
uv run scripts/AWS_START_STOP/deployment_status.py --summary

# Include AWS health checks (slower, requires AWS CLI)
uv run scripts/AWS_START_STOP/deployment_status.py --health

# Check specific module
uv run scripts/AWS_START_STOP/deployment_status.py --module 5_database

# JSON output for automation/scripting
uv run scripts/AWS_START_STOP/deployment_status.py --json
```

**What it shows:**
- Which terraform modules are deployed
- Number of resources in each module
- Monthly and daily cost estimates
- Last modification time
- Configuration readiness (terraform init, tfvars)
- Key outputs (URLs, ARNs)
- Health status of AWS resources (with `--health` flag)

**Example Output:**

```
📊 AWS DEPLOYMENT STATUS - ALEX PROJECT
======================================================================

Report Generated: 2025-11-26 17:15:45
AWS Region: us-east-1

📦 Overall Status:
   Total Modules: 7
   Deployed: 7
   Not Deployed: 0
   Total Resources: 80

💰 Cost Information:
   Current Monthly Cost: $136.00/month
   Current Daily Cost: $4.53/day
   Maximum Possible Cost: $136.00/month (if all deployed)

✅ Deployed Modules (7):

   ● Aurora Serverless v2 (5_database)
      Description: PostgreSQL database (0.5-1 ACU)
      Resources: 14
      Cost: $65/mo
      Last Modified: 2025-11-25 19:55:24

   [... more modules ...]

💡 Recommendations:
   ⚠️  High monthly costs ($136.00)
      Consider: uv run scripts/AWS_START_STOP/minimize_costs.py --mode shutdown
```

---

### 2. `minimize_costs.py` - Destroy Resources to Save Money

**Purpose:** Intelligently destroy AWS resources to minimize costs while preserving data.

**Features:**
- 🗑️ Three destruction modes (shutdown, minimal, full)
- 💰 Shows cost savings before executing
- 🔄 Handles dependencies correctly (reverse deployment order)
- 💾 Saves state for easy restoration
- 🛡️ Requires confirmation before destruction
- 📊 Dry-run mode to preview changes

**Usage:**

```bash
# Check current status and costs
uv run scripts/AWS_START_STOP/minimize_costs.py --status

# Destroy high-cost resources (Aurora + App Runner)
uv run scripts/AWS_START_STOP/minimize_costs.py --mode shutdown

# Preview shutdown without executing
uv run scripts/AWS_START_STOP/minimize_costs.py --mode shutdown --dry-run

# Destroy everything except S3 data
uv run scripts/AWS_START_STOP/minimize_costs.py --mode full
```

**Destruction Modes:**

| Mode | Destroys | Keeps Running | Monthly Savings |
|------|----------|---------------|-----------------|
| `shutdown` | Aurora + App Runner | Lambdas, S3, CloudFront, API Gateway | ~$116 |
| `minimal` | All expensive resources | S3 buckets, IAM roles (data preserved) | ~$135 |
| `full` | Everything | Nothing (S3 data preserved unless force-deleted) | ~$136 |

**Important Notes:**
- ⚠️ Always use `--status` first to see what will be affected
- 💾 State is saved to `.last_state.json` for restoration
- 🔄 Resources can be redeployed with `restart_infrastructure.py`
- 📦 S3 data is preserved unless you force-delete buckets

---

### 3. `restart_infrastructure.py` - Restore Destroyed Resources

**Purpose:** Restore AWS infrastructure that was previously destroyed for cost savings.

**Features:**
- 🔄 Restore from last destruction state
- 🎯 Preset configurations for common scenarios
- 🔗 Automatic dependency resolution
- ⏱️ Estimated deployment times
- 🎯 Module-specific restoration
- ✅ Post-deployment validation

**Usage:**

```bash
# Check what was destroyed last
uv run scripts/AWS_START_STOP/restart_infrastructure.py --status

# Restore everything from last destruction
uv run scripts/AWS_START_STOP/restart_infrastructure.py --all

# Restore specific modules
uv run scripts/AWS_START_STOP/restart_infrastructure.py --modules 5_database 6_agents

# Use a preset configuration
uv run scripts/AWS_START_STOP/restart_infrastructure.py --preset daily

# List available presets
uv run scripts/AWS_START_STOP/restart_infrastructure.py --list-presets
```

**Presets:**

| Preset | Modules | Use Case | Est. Time |
|--------|---------|----------|-----------|
| `daily` | Database + Agents | Daily development work | 15-22 min |
| `frontend` | Database + Agents + Frontend | Testing the full UI | 25-34 min |
| `research` | SageMaker + Researcher | Running research agent | 13-18 min |
| `full` | All modules | Full production-like environment | 40-50 min |

**Important Notes:**
- 📋 If database is deployed, remember to run seed data: `cd backend/database && uv run seed_data.py`
- 🔧 Ensure `terraform.tfvars` exists in each module directory
- ⏱️ Deployment times are estimates; actual times may vary
- 🔗 Dependencies are automatically resolved and deployed in correct order

---

### 4. `deploy_multi_cloud.py` - Multi-Cloud Deployment (AWS + GCP)

**Purpose:** Unified deployment tool for deploying to AWS, GCP, or both clouds simultaneously.

**Features:**
- ☁️ Deploy to AWS, GCP, or both
- 🔗 Automatic dependency resolution
- 💰 Cost estimation before deployment
- 🏥 Health checks after deployment
- 🎯 Module selection support
- 📊 Dry-run mode

**Usage:**

```bash
# Deploy everything to AWS
uv run scripts/AWS_START_STOP/deploy_multi_cloud.py --cloud aws --modules all

# Deploy database to GCP
uv run scripts/AWS_START_STOP/deploy_multi_cloud.py --cloud gcp --modules database

# Deploy to both clouds (database + agents)
uv run scripts/AWS_START_STOP/deploy_multi_cloud.py --cloud both --modules database,agents

# Dry run (preview without executing)
uv run scripts/AWS_START_STOP/deploy_multi_cloud.py --cloud both --modules all --dry-run
```

**Available Modules:**

**AWS:**
- `embeddings` - SageMaker Embeddings ($10/mo)
- `ingestion` - Document Ingestion ($1/mo)
- `researcher` - Research Agent ($51/mo)
- `database` - Aurora Database ($65/mo)
- `agents` - AI Agents (5 Lambdas) ($1/mo)
- `frontend` - Frontend (S3 + CloudFront) ($2/mo)
- `monitoring` - CloudWatch Monitoring ($6/mo)

**GCP:**
- `foundation` - GCP Foundation ($0/mo)
- `embeddings` - Vertex AI Embeddings ($3/mo)
- `database` - Cloud SQL Database ($30/mo)
- `agents` - Tagger Agent (Cloud Run) ($7/mo)

---

## Common Workflows

### Daily Development Workflow

```bash
# 1. Check current status
uv run scripts/AWS_START_STOP/deployment_status.py --summary

# 2. Start daily work (deploy database + agents)
uv run scripts/AWS_START_STOP/restart_infrastructure.py --preset daily

# 3. Work on your features...

# 4. End of day - shut down expensive resources
uv run scripts/AWS_START_STOP/minimize_costs.py --mode shutdown
```

### Weekend/Extended Break Workflow

```bash
# Friday end of day - destroy everything
uv run scripts/AWS_START_STOP/minimize_costs.py --mode full

# Monday morning - restore everything
uv run scripts/AWS_START_STOP/restart_infrastructure.py --all
```

### Check What's Running and Costing Money

```bash
# Full detailed report
uv run scripts/AWS_START_STOP/deployment_status.py

# Quick summary
uv run scripts/AWS_START_STOP/deployment_status.py --summary

# Include health checks to verify resources are working
uv run scripts/AWS_START_STOP/deployment_status.py --health
```

### Deploy Specific Module

```bash
# Check if it's already deployed
uv run scripts/AWS_START_STOP/deployment_status.py --module 5_database

# Deploy if needed
uv run scripts/AWS_START_STOP/restart_infrastructure.py --modules 5_database
```

---

## Cost Management Best Practices

1. **Check status regularly:**
   ```bash
   uv run scripts/AWS_START_STOP/deployment_status.py --summary
   ```

2. **Destroy expensive resources when not in use:**
   - Database (Aurora): $65/month - biggest cost!
   - App Runner: $51/month - second biggest
   - Combined savings: $116/month

3. **Use presets for quick starts:**
   - `daily` preset for normal development
   - `frontend` preset when testing UI
   - `research` preset for research agent work

4. **Monitor AWS billing console:**
   - Set up budget alerts
   - Check billing dashboard weekly
   - Review Cost Explorer for trends

5. **Weekend shutdowns:**
   - Friday EOD: `--mode full`
   - Monday morning: `--all` or `--preset daily`

---

## Troubleshooting

### "terraform.tfvars not found"

**Problem:** Module can't deploy because configuration is missing.

**Solution:**
```bash
cd terraform/<module_name>
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### "Terraform not initialized"

**Problem:** Terraform hasn't been initialized in the module directory.

**Solution:**
```bash
cd terraform/<module_name>
terraform init
```

### "Dependency failed"

**Problem:** A module depends on another module that isn't deployed.

**Solution:**
The scripts automatically resolve dependencies. If you see this error, deploy the dependency first:
```bash
# Check what's missing
uv run scripts/AWS_START_STOP/deployment_status.py

# Deploy dependencies
uv run scripts/AWS_START_STOP/restart_infrastructure.py --modules <dependency>
```

### "Health check failed"

**Problem:** AWS resources aren't responding or in expected state.

**Solution:**
1. Check AWS console for resource status
2. Check CloudWatch logs for errors
3. Verify IAM permissions
4. Wait a few minutes (resources may still be initializing)

### "Circular dependency detected"

**Problem:** The dependency resolution failed (shouldn't happen with these scripts).

**Solution:**
This indicates a bug in the module definitions. Report this issue and deploy modules individually in this order:
1. 2_sagemaker
2. 3_ingestion
3. 4_researcher
4. 5_database
5. 6_agents
6. 7_frontend
7. 8_enterprise

---

## Script Comparison

| Feature | deployment_status.py | minimize_costs.py | restart_infrastructure.py | deploy_multi_cloud.py |
|---------|---------------------|-------------------|---------------------------|----------------------|
| **Primary Purpose** | Check status | Destroy resources | Restore resources | Deploy multi-cloud |
| **Shows costs** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Shows resources** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Health checks** | ✅ Yes (optional) | ❌ No | ✅ After deploy | ✅ After deploy |
| **Dry-run mode** | N/A | ✅ Yes | N/A | ✅ Yes |
| **Multi-cloud** | ❌ AWS only | ❌ AWS only | ❌ AWS only | ✅ AWS + GCP |
| **JSON output** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Presets** | N/A | ✅ 3 modes | ✅ 4 presets | ❌ No |

**When to use each:**

- **deployment_status.py**: When you want to know "what's currently running and costing money?"
- **minimize_costs.py**: When you want to "save money by destroying resources"
- **restart_infrastructure.py**: When you want to "bring back destroyed resources"
- **deploy_multi_cloud.py**: When you want to "deploy to GCP or both clouds"

---

## Files Generated

These scripts generate state files in the `scripts/AWS_START_STOP/` directory:

- `.last_state.json` - Saved by `minimize_costs.py`, used by `restart_infrastructure.py`

⚠️ **Important:** Don't delete `.last_state.json` if you want to restore infrastructure with `--all` flag!

---

## Prerequisites

- Python 3.12+ with `uv` package manager
- AWS CLI configured with credentials
- Terraform installed and in PATH
- GCP CLI (for multi-cloud deployment only)

---

## Quick Reference

```bash
# Status check
uv run scripts/AWS_START_STOP/deployment_status.py --summary

# Shutdown for the day
uv run scripts/AWS_START_STOP/minimize_costs.py --mode shutdown

# Start the day
uv run scripts/AWS_START_STOP/restart_infrastructure.py --preset daily

# Deploy everything (first time)
uv run scripts/AWS_START_STOP/deploy_multi_cloud.py --cloud aws --modules all

# Full status with health
uv run scripts/AWS_START_STOP/deployment_status.py --health
```

---

## Support

For issues or questions:
1. Check this README
2. Review the guide in `/guides/` directory
3. Check AWS console for resource status
4. Review CloudWatch logs for errors

---

*Last Updated: November 2025*
*Project: Alex - Multi-Cloud AI Agent Platform*
