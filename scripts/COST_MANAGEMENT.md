# Cost Management Guide for Alex Infrastructure

This guide explains how to minimize AWS costs using the cost management scripts.

## Overview

The Alex project uses **73 AWS resources** across 7 terraform modules with an estimated monthly cost of **$136/month** ($4.53/day). The two most expensive resources are:

1. **Aurora Serverless v2 Database** - $65/month (~$2/day)
2. **App Runner Service** - $51/month (~$1.70/day)

These scripts help you destroy high-cost resources when not actively working, then quickly restore them when needed.

---

## Quick Start

### Check Current Costs
```bash
cd /home/kent_benson/AWS_projects/alex
uv run scripts/minimize_costs.py --status
```

### End of Day (Recommended)
Destroy Aurora + App Runner to save $116/month:
```bash
uv run scripts/minimize_costs.py --mode shutdown

### Start of Next Day
Restore database and agents for development:
```bash
# 1. Restore infrastructure
uv run scripts/restart_infrastructure.py --preset daily

# 2. Sync ARNs (CRITICAL if database was recreated)
uv run scripts/sync_arns.py

# 3. Seed the database
cd backend/database
uv run seed_data.py
```

**Important:** After recreating the database, ARNs change with a random suffix. You must sync ARNs before agents will work.

---

## Cost Minimization Script

**File:** `scripts/minimize_costs.py`

### Available Modes

#### 1. Shutdown Mode (Recommended Daily)
```bash
uv run scripts/minimize_costs.py --mode shutdown
```
- **Destroys:** Aurora database, App Runner service
- **Keeps:** Lambdas, S3, CloudFront, API Gateway
- **Savings:** $116/month (~$3.87/day)
- **Use case:** End of each work day

#### 2. Minimal Mode
```bash
uv run scripts/minimize_costs.py --mode minimal
```
- **Destroys:** All expensive resources (database, App Runner, SageMaker, dashboards)
- **Keeps:** S3 data (buckets preserved)
- **Savings:** $135/month (~$4.50/day)
- **Use case:** Weekend or extended break

#### 3. Full Mode
```bash
uv run scripts/minimize_costs.py --mode full
```
- **Destroys:** Everything
- **Keeps:** Nothing (S3 data preserved unless force-deleted)
- **Savings:** $136/month (~$4.53/day)
- **Use case:** Project pause or after course completion

### Options

```bash
# Preview without executing
uv run scripts/minimize_costs.py --mode shutdown --dry-run

# Skip confirmation prompts
uv run scripts/minimize_costs.py --mode shutdown --auto-approve

# Check current status
uv run scripts/minimize_costs.py --status
```

---

## Infrastructure Restart Script

**File:** `scripts/restart_infrastructure.py`
 
### Preset Configurations

#### Daily Development
```bash
uv run scripts/restart_infrastructure.py --preset daily
```
- **Deploys:** Database + Agent Lambdas
- **Time:** ~15-22 minutes
- **Use case:** Daily development work

#### Frontend Testing
```bash
uv run scripts/restart_infrastructure.py --preset frontend
```
- **Deploys:** Database + Agents + CloudFront
- **Time:** ~25-34 minutes
- **Use case:** Testing full UI

#### Research Work
```bash
uv run scripts/restart_infrastructure.py --preset research
```
- **Deploys:** SageMaker + App Runner
- **Time:** ~13-18 minutes
- **Use case:** Running research agent

#### Full Restoration
```bash
uv run scripts/restart_infrastructure.py --preset full
```
- **Deploys:** Everything
- **Time:** ~42-57 minutes
- **Use case:** Complete environment

### Other Options

```bash
# Restore specific modules
uv run scripts/restart_infrastructure.py --modules 5_database 6_agents

# Restore everything from last shutdown
uv run scripts/restart_infrastructure.py --all

# Check what was destroyed last
uv run scripts/restart_infrastructure.py --status

# List available presets
uv run scripts/restart_infrastructure.py --list-presets

# Skip confirmation prompts
uv run scripts/restart_infrastructure.py --preset daily --auto-approve
```

---

## Typical Daily Workflow

### Morning (Starting Work)
```bash
# 1. Check status
uv run scripts/minimize_costs.py --status

# 2. Restore infrastructure (with pre-flight validation)
uv run scripts/restart_infrastructure.py --preset daily

# 3. Sync ARNs (CRITICAL if database was recreated)
uv run scripts/sync_arns.py

# 4. Seed database (if destroyed last night)
cd backend/database
uv run seed_data.py

# 5. Start working!
```

### Evening (Ending Work)
```bash
# Destroy expensive resources
uv run scripts/minimize_costs.py --mode shutdown

# This saves $116/month (~$3.87/day) overnight
```

---

## Cost Breakdown by Module

| Module | Name | Monthly Cost | Can Idle? | Priority |
|--------|------|--------------|-----------|----------|
| 5_database | Aurora Serverless v2 | $65/mo | ❌ Always charges | 🔴 High |
| 4_researcher | App Runner Service | $51/mo | ❌ Always running | 🔴 High |
| 2_sagemaker | SageMaker Serverless | ~$10/mo | ✅ Pay-per-use | 🟡 Medium |
| 8_enterprise | CloudWatch Dashboards | $6/mo | ❌ Fixed cost | 🟡 Medium |
| 7_frontend | CloudFront + S3 + API GW | ~$2/mo | ✅ Pay-per-use | 🟢 Low |
| 6_agents | Lambda Functions + SQS | ~$1/mo | ✅ Pay-per-use | 🟢 Low |
| 3_ingestion | Ingestion Lambda | ~$1/mo | ✅ Pay-per-use | 🟢 Low |

**Total:** $136/month ($4.53/day)

---

## Resource Dependencies

Understanding dependencies helps avoid errors:

```
Frontend (7) ──┐
               ├──> Agents (6) ───> Database (5)
               │
               └──> Database (5)

Ingestion (3) ───> SageMaker (2)

Agents (6) ───> Ingestion (3) [optional - for vectors]

Researcher (4) - Independent

Enterprise (8) - Independent (monitoring only)
```

### Safe Destruction Order
1. Enterprise (8) - No dependencies
2. Frontend (7) - Depends on Agents & Database
3. Agents (6) - Depends on Database
4. Database (5) - Independent
5. Researcher (4) - Independent
6. Ingestion (3) - Independent
7. SageMaker (2) - Independent

### Safe Deployment Order
1. SageMaker (2) - No dependencies
2. Ingestion (3) - Needs SageMaker
3. Researcher (4) - Independent
4. Database (5) - Independent
5. Agents (6) - Needs Database
6. Frontend (7) - Needs Database & Agents
7. Enterprise (8) - Independent

---

## Important Notes

### Database ARN Synchronization (CRITICAL)
After deploying the database (5_database), ARNs change with a random 6-character suffix. You **must** sync ARNs:

```bash
uv run scripts/sync_arns.py
```

This updates `.env` files and `terraform.tfvars` with the new ARNs. Without this step, agents will get "AccessDenied" errors.

### Database Seeding
After deploying the database (5_database), you **must** seed it with initial data:

```bash
cd backend/database
uv run seed_data.py
```

This loads 22 ETF definitions required for the agents to function.

### Terraform State
- Each module has its own local `terraform.tfstate` file
- State files are in `.gitignore` and NOT committed
- If you lose state files, you may need to manually clean up AWS resources
- **New:** Scripts now validate state files for corruption and warn about empty/invalid states

### Pre-Flight Validation
The restart script now performs pre-flight checks before deployment:
- Verifies `terraform.tfvars` exists in each module
- Checks terraform is initialized (`.terraform/` directory exists)
- Fails fast with clear error messages if configuration is missing

### Timeout Protection
Terraform operations now have module-specific timeouts:
- **Database (5_database):** 30 minutes (Aurora scales from zero)
- **App Runner (4_researcher):** 15 minutes (container build)
- **Other modules:** 10 minutes (default)

This prevents operations from hanging indefinitely.

### Dependency Management
Scripts now automatically skip dependent modules if dependencies fail:
- If database (5) fails, agents (6) are automatically skipped
- If agents (6) fail, frontend (7) is automatically skipped
- Clear warnings show which modules were skipped and why

### S3 Data Preservation
- S3 buckets are **never** emptied by these scripts
- Your vector data, frontend assets, and Lambda packages are safe
- Only the terraform-managed infrastructure is destroyed

### Cost Monitoring
Always monitor your AWS costs in the AWS Console:
1. Go to AWS Billing Dashboard
2. Check "Cost Explorer" regularly
3. Verify your budget alerts are configured

---

## Troubleshooting

### "terraform.tfvars not found"
The pre-flight check now detects this before deployment starts:
```bash
cd terraform/X_module
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### "Failed to destroy module"
Some resources have dependencies. Common issues:
- S3 buckets must be empty (scripts handle this automatically)
- Database connections must be closed
- CloudFront distributions take 15-20 minutes to delete

Solution: Rerun the command, terraform will retry.

**Improved:** Scripts now log full terraform error output (stderr) for easier debugging.

### "Module already deployed"
The restart script detects already-deployed modules and skips them automatically.

### "State file corrupted" or "0 resources"
Scripts now detect and warn about corrupted or suspicious state files:
- Corrupted JSON: Returns clear error message
- Missing required fields: Warns and treats as not deployed
- Empty state (0 resources): Suspicious, treated as failed deployment

### "Dependency failed - skipping module"
Scripts now automatically skip dependent modules when dependencies fail:
- Example: If database (5) fails, agents (6) are automatically skipped
- This prevents cascading failures and wasted time

### Deployment Times Longer Than Expected
First deployments take longer:
- Aurora database: ~15 minutes (scales up from zero, 30min timeout)
- App Runner: ~10 minutes (builds container, 15min timeout)
- CloudFront: ~10 minutes (global distribution)

Subsequent deployments are faster as AWS caches resources.

**New:** Operations now have timeouts to prevent hanging indefinitely.

### "AccessDenied" or "NotAuthorized" after database recreation
This means ARNs are out of sync. Run:
```bash
uv run scripts/sync_arns.py
```

Database ARNs change with a random suffix every time you recreate them.

---

## Cost Optimization Tips

1. **Daily shutdown** saves the most with minimal effort ($116/month)
2. **Use presets** for common scenarios (faster than manual module selection)
3. **Weekend shutdown** saves additional costs during extended breaks
4. **Monitor AWS billing** regularly to catch unexpected charges
5. **Keep Lambdas and S3** - they're pay-per-use with minimal idle costs
6. **Don't destroy SageMaker** if actively developing ingestion (but ok to destroy overnight)

---

## Example: Week-Long Schedule

**Monday Morning:**
```bash
uv run scripts/restart_infrastructure.py --preset daily
uv run scripts/sync_arns.py
cd backend/database && uv run seed_data.py
```

**Monday-Friday Evening:**
```bash
uv run scripts/minimize_costs.py --mode shutdown
```

**Friday Evening (before weekend):**
```bash
uv run scripts/minimize_costs.py --mode minimal
```

**Monday Morning (after weekend):**
```bash
uv run scripts/restart_infrastructure.py --preset daily
uv run scripts/sync_arns.py
cd backend/database && uv run seed_data.py
```

**Weekly Savings:** ~$27/week (vs. always-on)

---

## Questions?

For issues with these scripts:
- Check the script output for error messages
- Review AWS CloudWatch logs for terraform errors
- Ensure Docker is running (if using package scripts)
- Verify AWS credentials: `aws sts get-caller-identity`

For course-related questions:
- Post in Udemy course forums
- Email instructor: ed@edwarddonner.com

---

## Recent Improvements

**December 2024 Update:**
- ✅ Added pre-flight validation (checks terraform.tfvars before deployment)
- ✅ Added timeout protection (30min for database, 15min for App Runner, 10min default)
- ✅ Added automatic dependency skipping (skip dependent modules if dependency fails)
- ✅ Added ARN sync warnings after database recreation
- ✅ Improved error logging (shows terraform stderr for debugging)
- ✅ Added state file validation (detects corrupted/empty states)
- ✅ Added atomic state file writes (prevents corruption)
- ✅ Improved cost terminology ("currently avoiding" vs "potential savings")

---

**Last Updated:** December 2024
**Course:** AI in Production (Weeks 3-4)
**Project:** Alex - Agentic Learning Equities eXplainer
