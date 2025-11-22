# VM Server Deployment Checklist

This checklist helps ensure all configuration is correct when running Alex on your VM server (instead of localhost).

## Problem Summary

When developing on a VM server but managing code from local machine, environment variables and configuration can get out of sync, causing services to fail silently.

## Pre-Flight Checklist

### 1. Environment Variables (.env file)

**Location:** `/home/kent_benson/AWS_projects/alex/.env`

**Critical variables for VM deployment:**

```bash
# Verify these are set (not empty):
grep "SQS_QUEUE_URL=" .env
grep "AURORA_CLUSTER_ARN=" .env
grep "AURORA_SECRET_ARN=" .env
grep "CLERK_JWKS_URL=" .env

# Should include VM IP in CORS:
grep "CORS_ORIGINS=" .env
# Expected: http://localhost:3000,http://34.71.165.144:3000
```

**Quick verification command:**
```bash
cd /home/kent_benson/AWS_projects/alex
cat .env | grep -E "SQS_QUEUE_URL|AURORA_CLUSTER_ARN|CORS_ORIGINS" | grep -v "^#"
```

### 2. Frontend Configuration

**Location:** `/home/kent_benson/AWS_projects/alex/frontend/.env.local`

```bash
# Must point to VM IP (not localhost):
NEXT_PUBLIC_API_URL=http://34.71.165.144:8000

# Clerk keys should be present:
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

**Verify:**
```bash
cd /home/kent_benson/AWS_projects/alex/frontend
grep "NEXT_PUBLIC_API_URL" .env.local
```

### 3. Running Services

**Check what's running:**
```bash
# Backend API (should be on port 8000):
ps aux | grep uvicorn | grep -v grep

# Frontend (should be on port 3000):
ps aux | grep "next-server\|node.*3000" | grep -v grep
```

## Starting Services on VM

### Start Backend API

```bash
cd /home/kent_benson/AWS_projects/alex/backend/api

# Verify .env is loaded (it's in parent directory)
export $(cat ../../.env | xargs)

# Start API
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verify it's working:**
```bash
curl http://34.71.165.144:8000/health
# Should return: {"status":"healthy"}
```

### Start Frontend

```bash
cd /home/kent_benson/AWS_projects/alex/frontend

# Verify .env.local exists
ls -la .env.local

# Start frontend
npm run dev
```

**Access in browser:**
```
http://34.71.165.144:3000
```

## Common Issues Checklist

### ✅ Job Analysis Never Completes

**Symptom:** Job stays in "pending" status forever

**Cause:** `SQS_QUEUE_URL` not set in `.env`

**Fix:**
```bash
# Get SQS URL from terraform:
cd terraform/6_agents
terraform output sqs_queue_url

# Add to .env:
# SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/393470797331/alex-analysis-jobs

# Restart backend API
```

### ✅ Clerk Deprecation Warnings

**Symptom:** Console shows "afterSignInUrl is deprecated"

**Cause:** Old environment variable naming in `.env.local`

**Fix:**
```bash
cd frontend
# Update .env.local:
# Use: NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
# Not: NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
```

### ✅ CORS Errors

**Symptom:** Browser console shows "CORS policy" errors

**Cause:** VM IP not in `CORS_ORIGINS`

**Fix:**
```bash
# In .env:
CORS_ORIGINS=http://localhost:3000,http://34.71.165.144:3000

# Restart backend API
```

### ✅ API Returns 403 Forbidden

**Symptom:** All API calls return "You don't have permission"

**Cause:** Clerk JWT validation misconfigured

**Fix:**
```bash
# Verify in .env:
CLERK_JWKS_URL=https://welcomed-gnu-92.clerk.accounts.dev/.well-known/jwks.json

# Restart backend API
```

## Environment Variable Source of Truth

**When running on VM, the `.env` file at project root is the source of truth:**

```
/home/kent_benson/AWS_projects/alex/.env  ← This one!
```

**After ANY changes to `.env`:**
1. Restart backend API (Ctrl+C, then restart)
2. Frontend will auto-reload (if using `npm run dev`)

## Verification After Changes

**Full system health check:**

```bash
# 1. Check backend health
curl http://34.71.165.144:8000/health

# 2. Check frontend is accessible
curl -I http://34.71.165.144:3000

# 3. Verify SQS queue exists
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/393470797331/alex-analysis-jobs \
  --attribute-names ApproximateNumberOfMessages

# 4. Check Lambda functions exist
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `alex-`)].FunctionName'
```

## Quick Reference: VM IP

**Current VM IP:** `34.71.165.144`

**Note:** This is non-static and may change if VM restarts!

If VM IP changes, update in:
- `.env` → `CORS_ORIGINS`
- `frontend/.env.local` → `NEXT_PUBLIC_API_URL`

## Getting Terraform Outputs

When you need ARNs, URLs, or other values from infrastructure:

```bash
# SQS Queue URL:
cd terraform/6_agents && terraform output sqs_queue_url

# Database ARNs:
cd terraform/5_database && terraform output

# API Gateway endpoints:
cd terraform/3_ingestion && terraform output
```

## Clean Restart Procedure

If things get weird, restart everything:

```bash
# 1. Stop all services (Ctrl+C in each terminal)

# 2. Verify nothing is running:
ps aux | grep -E "uvicorn|next-dev" | grep -v grep

# 3. Start backend:
cd /home/kent_benson/AWS_projects/alex/backend/api
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. In another terminal, start frontend:
cd /home/kent_benson/AWS_projects/alex/frontend
npm run dev

# 5. Test in browser:
# http://34.71.165.144:3000
```

## Notes

- Always work directly on the VM (via SSH or VS Code Remote SSH)
- Keep `.env` and `frontend/.env.local` in sync with VM IP
- After infrastructure changes (terraform apply), update `.env` with new ARNs/URLs
- Use `tmux` or `screen` to keep services running when you disconnect

---

**Last Updated:** 2025-11-22
**VM IP:** 34.71.165.144 (non-static)
