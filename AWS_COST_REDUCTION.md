# AWS Cost Reduction Guide

**Production URL:** https://d1hnrs9tdojzww.cloudfront.net
**Current Monthly Cost:** ~$50-75/month
**Last Updated:** November 23, 2025

---

## How Your AWS Application is Functioning

### Current Deployment Status: ✅ Fully Operational

Your Alex Financial Advisor is **live and running in production** with the following architecture:

```
User → CloudFront → S3 (Frontend)
                  → API Gateway → Lambda (API) → Aurora Database
                                               → SQS → Planner Lambda
                                                    → 5 Agent Lambdas
                                                    → Bedrock (Nova Pro)
                                                    → SageMaker (Embeddings)
                                                    → S3 Vectors
```

**Active Services (7 Terraform Modules Deployed):**

1. **Module 2: SageMaker** - Embedding endpoint (serverless)
2. **Module 3: Ingestion** - S3 Vectors + ingest Lambda
3. **Module 4: Researcher** - App Runner service (autonomous research)
4. **Module 5: Database** - Aurora Serverless v2 PostgreSQL
5. **Module 6: Agents** - 5 Lambda functions + SQS queue
6. **Module 7: Frontend** - CloudFront + S3 + API Gateway + API Lambda
7. **Module 8: Enterprise** - CloudWatch dashboards

**What's Running 24/7:**
- ✅ Aurora Serverless v2 database (biggest cost: $43-60/month)
- ✅ CloudFront CDN (serving your frontend)
- ✅ SageMaker serverless endpoint (billed per invocation)
- ✅ App Runner service for researcher (optional scheduler)
- ✅ All Lambda functions (billed per execution only)
- ✅ API Gateway (billed per request)

---

## Current Cost Breakdown

| Service | Monthly Cost | Usage Pattern |
|---------|-------------|---------------|
| **Aurora Serverless v2** | $43-60 | Always-on (0.5-1 ACU) |
| **Lambda Functions** | $1-5 | Per-invocation only |
| **API Gateway** | $3-4 | Per-request (1M free) |
| **SageMaker Serverless** | $1-3 | Per-invocation only |
| **App Runner** | $5-10 | Always-on (minimal) |
| **S3 + CloudFront** | $1-2 | Storage + CDN |
| **Bedrock (Nova Pro)** | $0.01-0.10 | Per analysis |
| **SQS** | $0.40 | Per-message (1M free) |
| **CloudWatch** | $2-5 | Logs + metrics |
| **TOTAL** | **$50-75** | |

---

## Cost Reduction Strategies

### Option 1: Destroy Database When Not Using (Saves $43-60/month)

**Impact:** Reduces cost to ~$10-15/month
**Downside:** App won't work until database is recreated

```bash
# Navigate to database module
cd /home/kent_benson/AWS_projects/alex/terraform/5_database

# Destroy the database
terraform destroy

# To restart later:
terraform apply
# Then re-run migrations:
cd ../../backend/database
uv run run_migrations.py
uv run load_seed_data.py
```

**When to use:**
- During breaks from development (weekends, vacations)
- When testing/learning is complete
- Before final project handoff

**Time to recreate:** 10-15 minutes

---

### Option 2: Stop App Runner Service (Saves $5-10/month)

**Impact:** Disables autonomous researcher (optional feature)
**Downside:** No automated market research updates

```bash
# Navigate to researcher module
cd /home/kent_benson/AWS_projects/alex/terraform/4_researcher

# Destroy App Runner service
terraform destroy

# To restart later:
terraform apply
```

**When to use:**
- If you don't need automated research
- Research agent can still be invoked manually

---

### Option 3: Reduce Aurora Capacity (Saves $20-30/month)

**Impact:** Database runs on minimal resources
**Downside:** Slower performance, might not handle high load

Currently configured for 0.5-1 ACU. Can reduce to minimum:

Edit `terraform/5_database/main.tf`:
```hcl
serverlessv2_scaling_configuration {
  max_capacity = 0.5   # Reduce from 1 to 0.5
  min_capacity = 0.5   # Keep at minimum
}
```

Then apply:
```bash
cd terraform/5_database
terraform apply
```

---

### Option 4: Destroy Entire Stack (Saves $50-75/month = $0)

**Impact:** Completely removes all AWS infrastructure
**Downside:** App is offline, data is deleted

```bash
# Destroy in reverse order (8 → 7 → 6 → 5 → 4 → 3 → 2)
cd /home/kent_benson/AWS_projects/alex

# Module 8: Enterprise (CloudWatch dashboards)
cd terraform/8_enterprise && terraform destroy && cd ..

# Module 7: Frontend (CloudFront, S3, API Gateway)
cd terraform/7_frontend && terraform destroy && cd ..

# Module 6: Agents (5 Lambdas + SQS)
cd terraform/6_agents && terraform destroy && cd ..

# Module 5: Database (Aurora - BIGGEST SAVINGS)
cd terraform/5_database && terraform destroy && cd ..

# Module 4: Researcher (App Runner)
cd terraform/4_researcher && terraform destroy && cd ..

# Module 3: Ingestion (S3 Vectors + Lambda)
cd terraform/3_ingestion && terraform destroy && cd ..

# Module 2: SageMaker (Embeddings)
cd terraform/2_sagemaker && terraform destroy && cd ..
```

**When to use:**
- Project is complete and submitted
- Switching to GCP permanently
- Long-term hiatus from development

**Time to recreate:** 2-3 hours (following all 8 guides again)

---

### Option 5: Pause Development, Keep Core Running

**Recommended for cost-conscious development:**

**Keep running:**
- Frontend (CloudFront + S3): ~$1/month
- Database: ~$43/month
- Core agents: $0 when idle

**Destroy:**
- App Runner researcher: Saves $5-10/month
- CloudWatch dashboards: Saves $2-5/month

**Total cost:** ~$44-50/month (saves $6-25/month)

```bash
# Destroy optional components
cd terraform/8_enterprise && terraform destroy
cd ../4_researcher && terraform destroy
```

---

## Monitoring Your Costs

### Check Current Spending

```bash
# AWS CLI command to see current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

### AWS Console
1. Sign in as root user
2. Click account name (top right) → **Billing Dashboard**
3. View **Bills** for current month breakdown
4. Check **Budgets** for your configured alerts

### CloudWatch Dashboards
- [AI Model Usage](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=alex-ai-model-usage)
- [Agent Performance](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=alex-agent-performance)

---

## Understanding What's Costing You Money

### Always-On Services (Fixed Costs)
1. **Aurora Database** - $43-60/month (0.5-1 ACU)
   - Runs 24/7 even when not used
   - Scales automatically with load
   - **Action:** Destroy when not developing

2. **App Runner** - $5-10/month
   - Researcher service always ready
   - Optional feature
   - **Action:** Can safely destroy

3. **CloudFront CDN** - $1-2/month
   - Serves your frontend globally
   - Needed for app to work
   - **Action:** Keep if app should stay online

### Pay-Per-Use Services (Variable Costs)
1. **Lambda Functions** - $0 when idle
   - Only charged per execution
   - First 1M requests/month free
   - **Action:** No action needed (cheap)

2. **Bedrock API** - $0.01-0.10 per analysis
   - Only charged when generating reports
   - Nova Pro pricing: ~$0.004/1000 input tokens
   - **Action:** No action needed (cheap)

3. **SageMaker Serverless** - $0 when idle
   - Only charged per embedding invocation
   - Scales to zero automatically
   - **Action:** No action needed (cheap)

4. **API Gateway** - $3-4/month
   - Per-request billing
   - 1M requests free tier
   - **Action:** No action needed

---

## Free Tier Status

After 12 months, AWS Free Tier expires. Check if you're still in free tier:

```bash
# Check account creation date
aws iam get-user --query 'User.CreateDate' --output text
```

If account is > 12 months old:
- Lambda: Still 1M requests/month free (permanent)
- API Gateway: First 1M requests free (permanent)
- S3: Storage costs apply (no longer free)
- CloudFront: Data transfer costs apply
- Aurora: No free tier (always paid)

---

## Cost Alerts

You should have billing alerts configured at:
- 50% of budget
- 80% of budget
- 100% of budget

To verify:
1. AWS Console → Billing → Budgets
2. Check email for alert notifications

To modify:
1. Billing → Budgets → Select your budget → Edit

---

## Recommended Strategy for Your Situation

### If Still Learning/Developing
**Keep everything running** - Convenience > Cost savings
- Total: ~$50-75/month
- App always accessible
- Can test anytime

### If Taking a Break (1-2 weeks)
**Destroy database only**
- Saves: $43-60/month
- Keep: Frontend, Lambdas (minimal cost)
- Can restore in 15 minutes when needed

### If Project Complete
**Destroy everything**
- Saves: $50-75/month (down to $0)
- Export database first if you want data
- Can recreate later using terraform

---

## How to Export Database Before Destroying

```bash
# Connect to Aurora and export data
cd /home/kent_benson/AWS_projects/alex/backend/database

# Create backup
uv run python -c "
from database import Database
import json

db = Database()

# Export all tables
backup = {
    'users': db.users.list_all(),
    'accounts': db.accounts.list_all(),
    'positions': db.positions.list_all(),
    'instruments': db.instruments.list_all(),
    'jobs': db.jobs.list_all()
}

with open('database_backup.json', 'w') as f:
    json.dump(backup, f, indent=2, default=str)

print('✅ Backup saved to database_backup.json')
"
```

---

## Quick Commands Reference

```bash
# Check which modules are deployed
ls -la /home/kent_benson/AWS_projects/alex/terraform/*/terraform.tfstate

# Destroy database only (biggest savings)
cd /home/kent_benson/AWS_projects/alex/terraform/5_database
terraform destroy

# Destroy everything (reverse order)
cd /home/kent_benson/AWS_projects/alex
for module in 8_enterprise 7_frontend 6_agents 5_database 4_researcher 3_ingestion 2_sagemaker; do
  cd terraform/$module && terraform destroy -auto-approve && cd ../..
done

# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

---

## Support Resources

- **AWS Support:** https://console.aws.amazon.com/support
- **Cost Explorer:** https://console.aws.amazon.com/cost-management/home
- **Billing Dashboard:** https://console.aws.amazon.com/billing
- **CloudWatch Dashboards:** https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:

---

**Recommendation:**

For your current situation (learning complete, considering GCP migration):

1. **Export database backup** (5 minutes)
2. **Destroy database** - Saves $43-60/month immediately
3. **Keep frontend online** - Only costs $1-5/month for demos
4. **Destroy completely** when GCP is ready OR project is submitted

**This reduces cost from $50-75/month → $1-5/month while keeping the app accessible for demonstrations.**

---

**Document Version:** 1.0
**Last Updated:** November 23, 2025
