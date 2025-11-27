# GitHub PR Deployment Testing - Setup Checklist

## ✅ Implementation Complete

All code changes have been implemented. This document provides the next steps for activating deployment testing.

## Files Created/Modified

### Created:
- ✅ `.github/workflows/deployment-tests.yml` - Deployment test workflow
- ✅ `.github/workflows/README.md` - Complete setup guide with IAM policy template

### Modified:
- ✅ `.github/workflows/test.yml` - Added clarifying comments
- ✅ `CLAUDE.md` - Added GitHub Actions CI/CD section
- ✅ `README.md` - Added workflow status badges

## Next Steps (Manual Configuration Required)

### 1. Create IAM User (AWS Console)

**Time:** ~5-10 minutes

Navigate to AWS Console → IAM → Users → Create user

1. **User name:** `github-actions-testing`
2. **Access type:** Programmatic access
3. **Permissions:** Create and attach custom policy (see `.github/workflows/README.md` for full policy JSON)
4. **Generate access keys** and save them securely

**Key permissions needed:**
- RDS Data API execute
- Secrets Manager read
- Lambda invoke
- SQS send/receive
- Bedrock invoke (Nova Pro)
- CloudWatch Logs read
- S3 read (vectors bucket)
- SageMaker invoke endpoint

### 2. Get ARN Values (Local Terminal)

**Time:** ~2 minutes

```bash
# Get database ARNs
cd terraform/5_database
terraform output

# Get agent ARNs
cd ../6_agents
terraform output

# Get SageMaker endpoint
cd ../2_sagemaker
terraform output

# Get S3 vectors bucket
cd ../3_ingestion
terraform output

# OR use verify script to see all at once:
cd /home/kent_benson/AWS_projects/alex
uv run scripts/verify_arns.py
```

**Copy these values:**
- `aurora_cluster_arn`
- `aurora_secret_arn` (note the random suffix!)
- `database_name` (should be "alex")
- `sqs_queue_url`
- `endpoint_name` (SageMaker)
- `vector_bucket`

### 3. Configure GitHub Secrets (GitHub Repository)

**Time:** ~5 minutes

Navigate to: **GitHub Repository → Settings → Secrets and variables → Actions**

Add these 12 secrets (click "New repository secret" for each):

```
AWS_ACCESS_KEY_ID           → From Step 1 (IAM access key)
AWS_SECRET_ACCESS_KEY       → From Step 1 (IAM secret key)
AWS_ACCOUNT_ID              → Your AWS account ID (12 digits)
AWS_REGION                  → us-east-1 (or your region)
AURORA_CLUSTER_ARN          → From Step 2 (terraform output)
AURORA_SECRET_ARN           → From Step 2 (terraform output - has random suffix!)
AURORA_DATABASE             → alex
SQS_QUEUE_URL              → From Step 2 (terraform output)
BEDROCK_MODEL_ID           → us.amazon.nova-pro-v1:0
BEDROCK_REGION             → us-west-2 (or your Bedrock region)
SAGEMAKER_ENDPOINT         → alex-embedding-endpoint (from Step 2)
VECTOR_BUCKET              → alex-vectors-<account-id> (from Step 2)
```

### 4. Test the Workflows (GitHub Actions)

**Time:** ~15 minutes

#### Option A: Manual Trigger (Recommended First)

1. Go to **Actions** tab in your GitHub repository
2. Select **Deployment Tests (AWS)** workflow
3. Click **Run workflow** → Select current branch → **Run workflow**
4. Monitor execution (should take ~10-15 minutes)
5. Verify all jobs pass ✅

#### Option B: Test via PR

```bash
# Create test branch
uv run KB_github_UTILITIES/git_utilities/github_new_branch.py
# Enter name: test-ci-deployment

# Make trivial change
echo "# CI Test" >> README.md
git add README.md
git commit -m "Test: Trigger deployment tests"
git push

# Go to GitHub and create PR from test-ci-deployment to main
# Both workflows should trigger automatically
```

### 5. Enable Branch Protection (Optional but Recommended)

**Time:** ~3 minutes

Navigate to: **GitHub Repository → Settings → Branches → Branch protection rules**

1. Add rule for `main` branch
2. Enable: "Require status checks to pass before merging"
3. Select ALL these required checks:
   - Backend Tests - database
   - Backend Tests - planner
   - Backend Tests - tagger
   - Backend Tests - reporter
   - Backend Tests - charter
   - Backend Tests - retirement
   - Frontend Unit Tests
   - Frontend E2E Tests
   - Deploy Test - planner ← NEW
   - Deploy Test - tagger ← NEW
   - Deploy Test - reporter ← NEW
   - Deploy Test - charter ← NEW
   - Deploy Test - retirement ← NEW
   - Deploy Test - Database ← NEW
   - Deploy Test - Ingest ← NEW

---

## Quick Reference

### Workflow Triggers

**Mock Tests** (`test.yml`):
- Triggers: Push to main/develop, all PRs
- Runtime: ~2-5 minutes
- AWS: Not required

**Deployment Tests** (`deployment-tests.yml`):
- Triggers: PRs to main/develop, manual dispatch
- Runtime: ~10-15 minutes
- AWS: Required (deployed infrastructure + credentials)

### What Gets Tested

**Mock Tests:**
- Backend agents with mocked AWS services
- Frontend Jest unit tests
- Frontend Playwright E2E tests
- Linting (non-blocking)

**Deployment Tests:**
- All 5 agents against real Lambda functions
- Database connectivity (Aurora Data API)
- S3 Vectors ingestion and search
- Real Bedrock Nova Pro inference
- SQS queue operations

### Cost per PR

- Mock tests: Free (GitHub Actions free tier)
- Deployment tests: ~$0.06-0.12 per PR commit
- Total runtime: ~12-20 minutes per PR

---

## Maintenance Tasks

### When You Recreate Infrastructure

**CRITICAL:** If you run `terraform destroy` then `terraform apply` on database or agents, you MUST:

1. Get new ARNs:
   ```bash
   cd terraform/5_database && terraform output
   cd terraform/6_agents && terraform output
   ```

2. Update GitHub secrets with new `AURORA_CLUSTER_ARN` and `AURORA_SECRET_ARN`

3. Why: Aurora secret ARN has a random 6-character suffix that changes on recreation

### Rotate IAM Credentials

**Frequency:** Every 90 days

1. AWS Console → IAM → Users → github-actions-testing → Security credentials
2. Create new access key
3. Update `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in GitHub secrets
4. Test with manual workflow trigger
5. Delete old access key

---

## Troubleshooting

### "AccessDenied" Errors in Deployment Tests

**Cause:** Stale ARNs after infrastructure recreation

**Fix:**
```bash
uv run scripts/verify_arns.py  # Check current values
# Compare with GitHub secrets
# Update mismatched secrets
```

### "Model not found" Bedrock Errors

**Cause:** Bedrock model access not granted

**Fix:**
1. AWS Console → Bedrock → Model access
2. Request access to Nova Pro in `BEDROCK_REGION`
3. For inference profiles, grant access in multiple regions

### Tests Timeout

**Cause:** Cold Lambda starts or Bedrock throttling

**Fix:**
1. Workflow timeout is 20 minutes (configurable in deployment-tests.yml)
2. Check CloudWatch logs for throttling
3. Request higher Bedrock quotas if needed

### Secrets Not Working

**Verify:**
```bash
# Check secrets are set (won't show values)
# GitHub → Settings → Secrets → Actions
# Should show 12 secrets

# Test locally with same values
cd backend/planner
export AWS_REGION_NAME=<BEDROCK_REGION>
export AURORA_CLUSTER_ARN=<value>
export AURORA_SECRET_ARN=<value>
# ... etc
uv run pytest test_full.py -v
```

---

## Documentation References

- **Complete setup guide:** `.github/workflows/README.md`
- **CI/CD documentation:** `CLAUDE.md` (GitHub Actions CI/CD section)
- **IAM policy template:** `.github/workflows/README.md` (Step 1.2)
- **Testing guide:** `TESTING_CODE_GUIDES/TESTING_QUICK_REFERENCE.md`

---

## Summary

You now have:
- ✅ Deployment test workflow ready to use
- ✅ Mock tests with clarifying comments
- ✅ Documentation in CLAUDE.md
- ✅ Status badges in README.md
- ✅ Complete setup guide with IAM policy template

**Next action:** Complete Steps 1-4 above to activate deployment testing on PRs.

**Estimated time:** ~20-30 minutes for complete setup

**Result:** Every PR will automatically run comprehensive deployment tests against your real AWS infrastructure, catching issues before merge.
