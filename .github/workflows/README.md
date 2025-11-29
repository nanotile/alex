# GitHub Actions Workflows

This directory contains CI/CD workflows for the Alex project.

## Workflows

### test.yml - Mock Tests (Fast)
**Triggers:** Push to main/develop, all PRs
**Runtime:** ~2-5 minutes
**AWS Required:** No

Runs fast mock-based tests that don't require AWS infrastructure:
- Backend tests with mocked services (`MOCK_LAMBDAS=true`)
- Frontend Jest unit tests
- Frontend Playwright E2E tests
- Linting and type checking

### deployment-tests.yml - Deployment Tests (Comprehensive)
**Triggers:** Pull requests to main/develop, manual dispatch
**Runtime:** ~10-15 minutes
**AWS Required:** Yes (deployed infrastructure + credentials)

Runs comprehensive deployment tests against real AWS infrastructure:
- Backend `test_full.py` for all agents (planner, tagger, reporter, charter, retirement)
- Database connectivity tests (`test_data_api.py`)
- S3 Vectors ingestion tests
- Tests actual Lambda functions, Aurora, SQS, Bedrock

---

## Setup Guide

### Prerequisites
- AWS infrastructure deployed (Guides 2-6)
- AWS account with deployed Alex resources
- GitHub repository admin access

### Step 1: Create IAM User for GitHub Actions

#### 1.1 Create User
Navigate to AWS Console → IAM → Users → Create user

- **User name:** `github-actions-testing`
- **Access type:** Programmatic access (access keys)
- **Permissions:** Attach custom policy (see below)

#### 1.2 Create Custom IAM Policy

**Policy name:** `GitHubActionsTestingPolicy`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RDSDataAPIAccess",
      "Effect": "Allow",
      "Action": [
        "rds-data:ExecuteStatement",
        "rds-data:BatchExecuteStatement",
        "rds-data:BeginTransaction",
        "rds-data:CommitTransaction",
        "rds-data:RollbackTransaction"
      ],
      "Resource": [
        "arn:aws:rds:*:*:cluster:alex-aurora-cluster"
      ]
    },
    {
      "Sid": "SecretsManagerAccess",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:*:*:secret:alex-aurora-credentials-*"
      ]
    },
    {
      "Sid": "LambdaInvokeAccess",
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:*:*:function:alex-*"
      ]
    },
    {
      "Sid": "SQSAccess",
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl"
      ],
      "Resource": [
        "arn:aws:sqs:*:*:alex-analysis-jobs"
      ]
    },
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
        "arn:aws:bedrock:*::foundation-model/us.amazon.nova-pro-v1:0",
        "arn:aws:bedrock:*::foundation-model/eu.amazon.nova-pro-v1:0"
      ]
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:FilterLogEvents",
        "logs:GetLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/lambda/alex-*"
      ]
    },
    {
      "Sid": "S3VectorsReadAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::alex-vectors-*",
        "arn:aws:s3:::alex-vectors-*/*"
      ]
    },
    {
      "Sid": "SageMakerEndpointAccess",
      "Effect": "Allow",
      "Action": [
        "sagemaker:InvokeEndpoint"
      ],
      "Resource": [
        "arn:aws:sagemaker:*:*:endpoint/alex-embedding-endpoint"
      ]
    }
  ]
}
```

#### 1.3 Generate Access Keys
1. After creating user, go to **Security credentials** tab
2. Click **Create access key**
3. Select **Third-party service** use case
4. Save `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (shown once only!)

---

### Step 2: Get AWS Resource ARNs

Run these commands locally to get ARN values for GitHub secrets:

```bash
# Navigate to terraform directories and get outputs
cd terraform/5_database
terraform output

# Expected outputs:
# aurora_cluster_arn = "arn:aws:rds:us-east-1:123456789012:cluster:alex-aurora-cluster"
# aurora_secret_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:alex-aurora-credentials-abc123-XyZ789"
# database_name = "alex"

cd ../6_agents
terraform output

# Expected outputs:
# sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/alex-analysis-jobs"
# planner_function_name = "alex-planner"
# tagger_function_name = "alex-tagger"
# reporter_function_name = "alex-reporter"
# charter_function_name = "alex-charter"
# retirement_function_name = "alex-retirement"

cd ../2_sagemaker
terraform output

# Expected outputs:
# endpoint_name = "alex-embedding-endpoint"

cd ../3_ingestion
terraform output

# Expected outputs:
# vector_bucket = "alex-vectors-123456789012"
```

**Alternative:** Use the verify script to see all values at once:
```bash
cd /home/kent_benson/AWS_projects/alex
uv run scripts/verify_arns.py
```

---

### Step 3: Configure GitHub Repository Secrets

Navigate to: **GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

Add each of the following secrets:

| Secret Name | Example Value | Source |
|-------------|---------------|--------|
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | IAM user access key (Step 1.3) |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | IAM user secret key (Step 1.3) |
| `AWS_ACCOUNT_ID` | `123456789012` | Your AWS account ID |
| `AWS_REGION` | `us-east-1` | Your primary AWS region |
| `AURORA_CLUSTER_ARN` | `arn:aws:rds:us-east-1:123:cluster:alex-aurora-cluster` | terraform/5_database output |
| `AURORA_SECRET_ARN` | `arn:aws:secretsmanager:us-east-1:123:secret:alex-aurora-credentials-abc123-XyZ789` | terraform/5_database output |
| `AURORA_DATABASE` | `alex` | Database name (always "alex") |
| `SQS_QUEUE_URL` | `https://sqs.us-east-1.amazonaws.com/123/alex-analysis-jobs` | terraform/6_agents output |
| `BEDROCK_MODEL_ID` | `us.amazon.nova-pro-v1:0` | Nova Pro model ID for your region |
| `BEDROCK_REGION` | `us-west-2` | Region where Bedrock is available |
| `SAGEMAKER_ENDPOINT` | `alex-embedding-endpoint` | terraform/2_sagemaker output |
| `VECTOR_BUCKET` | `alex-vectors-123456789012` | terraform/3_ingestion output |

---

### Step 4: Test the Workflows

#### 4.1 Manual Test (Recommended First)

1. Go to **Actions** tab in GitHub
2. Select **Deployment Tests (AWS)** workflow
3. Click **Run workflow**
4. Select your current branch
5. Click **Run workflow**
6. Monitor the workflow execution
7. Verify all jobs pass

#### 4.2 Automatic Test via PR

```bash
# Create a test branch
uv run KB_github_UTILITIES/git_utilities/github_new_branch.py
# Name: test-ci-deployment

# Make a trivial change
echo "# CI Test" >> README.md
git add README.md
git commit -m "Test: Trigger deployment tests"
git push

# Create PR on GitHub and verify both workflows run
```

---

### Step 5: Enable Branch Protection (Optional but Recommended)

Navigate to: **GitHub Repository → Settings → Branches → Add branch protection rule**

**Branch name pattern:** `main`

**Enable these settings:**
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging

**Select required status checks:**
- `Backend Tests - database`
- `Backend Tests - planner`
- `Backend Tests - tagger`
- `Backend Tests - reporter`
- `Backend Tests - charter`
- `Backend Tests - retirement`
- `Frontend Unit Tests`
- `Frontend E2E Tests`
- `Deploy Test - planner`
- `Deploy Test - tagger`
- `Deploy Test - reporter`
- `Deploy Test - charter`
- `Deploy Test - retirement`
- `Deploy Test - Database`
- `Deploy Test - Ingest`

---

## Maintenance

### Updating Secrets After Infrastructure Recreation

**When:** After running `terraform destroy` + `terraform apply` on database or agents

**Why:** Aurora secret ARN suffix changes every time the database is recreated

**How:**
1. Get new ARNs:
   ```bash
   cd terraform/5_database && terraform output
   cd terraform/6_agents && terraform output
   ```
2. Update GitHub secrets with new values for:
   - `AURORA_CLUSTER_ARN`
   - `AURORA_SECRET_ARN`
   - `SQS_QUEUE_URL` (if recreated)
3. Test with manual workflow trigger

### Rotating IAM Credentials

**Frequency:** Every 90 days (recommended)

**Process:**
1. AWS Console → IAM → Users → github-actions-testing
2. Security credentials → Create access key
3. Update `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in GitHub secrets
4. Test workflow
5. Delete old access key in AWS Console

---

## Troubleshooting

### Deployment Tests Failing with "AccessDenied"

**Cause:** Stale ARNs in GitHub secrets after infrastructure recreation

**Fix:**
1. Run `uv run scripts/verify_arns.py` locally to see current values
2. Compare with GitHub secrets
3. Update mismatched secrets

### "Model not found" or Bedrock Errors

**Cause:** Bedrock model access not granted or wrong region

**Fix:**
1. AWS Console → Bedrock → Model access
2. Request access to Nova Pro in the region specified in `BEDROCK_REGION`
3. For inference profiles, ensure access in multiple regions

### CloudWatch Logs Not Uploading

**Cause:** IAM policy missing CloudWatch Logs permissions

**Fix:**
1. Verify IAM policy includes `logs:FilterLogEvents` and `logs:GetLogEvents`
2. Check log group exists: `/aws/lambda/alex-{agent-name}`

### Tests Timing Out

**Cause:** Lambda functions cold-starting or Bedrock rate limits

**Fix:**
1. Increase timeout in workflow (currently 20 minutes for agents)
2. Check for Bedrock throttling in CloudWatch logs
3. Consider request access to higher Bedrock quotas

---

## Cost Considerations

### Per PR Run Costs

| Service | Cost per Test | Notes |
|---------|---------------|-------|
| Bedrock Inference | $0.05-0.10 | 5 agents × 2-3 inferences each |
| Aurora Data API | $0.01 | Minimal data transfer |
| Lambda Invocations | $0.001 | Within free tier typically |
| CloudWatch Logs | Negligible | Small log volumes |
| **Total** | **~$0.06-0.12** | Per PR commit |

### GitHub Actions Minutes

- Mock tests: ~2-5 minutes (free tier: 2000 min/month)
- Deployment tests: ~10-15 minutes
- **Total per PR:** ~12-20 minutes

**Cost optimization:**
- Run deployment tests only on PRs (not every push to main)
- Use `workflow_dispatch` for manual-only triggers if needed
- Skip tests for docs-only PRs using path filters

---

## Future Enhancements

Potential improvements for the CI/CD pipeline:

1. **AWS OIDC Integration** - Replace static credentials with OpenID Connect (more secure, no long-lived keys)
2. **Terraform Validation** - Add workflow to validate Terraform syntax and plans
3. **Security Scanning** - Integrate Snyk, CodeQL, or other security scanners
4. **Test Result Caching** - Cache uv dependencies and test results
5. **Performance Benchmarking** - Track agent response times over commits
6. **Separate Researcher Tests** - Researcher agent has longer runtime, could be separate workflow
7. **Deployment Test Coverage** - Track coverage for deployment tests separately

---

## Support

For issues with GitHub Actions workflows:
1. Check workflow run logs in GitHub Actions tab
2. Verify all secrets are correctly configured
3. Test locally with `uv run pytest test_full.py` to isolate issues
4. Check AWS CloudWatch logs for Lambda/Bedrock errors

For questions about the Alex project setup, see main README.md and CLAUDE.md.
