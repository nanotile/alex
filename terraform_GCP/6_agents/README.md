# Module 6: Tagger Agent on Cloud Run

Deploy the Tagger classification agent as a containerized service on Google Cloud Run.

## Overview

This module deploys the Tagger agent that classifies financial instruments (ETFs, stocks, bonds) with detailed allocation breakdowns. The agent:
- Uses AWS Bedrock (Nova Pro) for AI classification
- Stores results in Cloud SQL database
- Runs as a containerized FastAPI service on Cloud Run
- Auto-scales from 0 to N instances based on load

## Architecture

```
Internet → Cloud Run (Tagger) → Cloud SQL
                ↓
           AWS Bedrock (Nova Pro)
```

## Prerequisites

### 1. Docker Image Built and Pushed

The Docker image must be in GCP Artifact Registry:

```bash
cd backend/tagger_gcp
python build_and_push.py
```

This will create: `us-central1-docker.pkg.dev/PROJECT/alex-gcl-docker-repo/tagger-agent:latest`

### 2. Database Deployed

Cloud SQL must be running (from Module 5):

```bash
cd terraform_GCP/5_database
terraform output cloud_sql_instance_connection_name
```

### 3. AWS Bedrock Access

Ensure AWS credentials are available and Bedrock model access is granted:
- Model: `us.amazon.nova-pro-v1:0`
- Region: `us-west-2` (or your preferred region)
- Check: https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/modelaccess

## Configuration

1. **Copy the example configuration**:
```bash
cp terraform.tfvars.example terraform.tfvars
```

2. **Edit `terraform.tfvars`** with your values:
```hcl
# GCP Configuration
gcp_project = "gen-lang-client-0259050339"
gcp_region  = "us-central1"

# Cloud SQL (get from Module 5 output)
cloud_sql_instance_connection_name = "gen-lang-client-0259050339:us-central1:alex-demo-db"
cloud_sql_database                 = "alex"
cloud_sql_user                     = "alex_admin"
cloud_sql_password_secret_name     = "alex-db-password"

# AWS Bedrock
bedrock_model_id = "us.amazon.nova-pro-v1:0"
bedrock_region   = "us-west-2"

# Docker Image (from build_and_push.py output)
docker_image = "us-central1-docker.pkg.dev/gen-lang-client-0259050339/alex-gcl-docker-repo/tagger-agent:latest"

# Cloud Run Settings
service_name          = "tagger-agent"
max_instances         = 3
min_instances         = 0    # Scale to zero when idle
cpu                   = "1"
memory                = "512Mi"
timeout_seconds       = 300  # 5 minutes
allow_unauthenticated = true # For demo purposes
```

## Deployment

### 1. Initialize Terraform
```bash
terraform init
```

### 2. Review the Plan
```bash
terraform plan
```

Expected resources:
- 1 Cloud Run service
- 2 IAM bindings (Secret Manager + Cloud SQL access)
- 1 IAM member (public access for demo)

### 3. Apply Configuration
```bash
terraform apply
```

This takes ~2-3 minutes to:
- Deploy Cloud Run service
- Configure IAM permissions
- Set environment variables

### 4. Get Service URL
```bash
terraform output service_url
```

Example output: `https://tagger-agent-xxxxx-uc.a.run.app`

## Testing

### 1. Health Check

```bash
SERVICE_URL=$(terraform output -raw service_url)
curl $SERVICE_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "checks": {
    "db_query": "passed"
  }
}
```

### 2. Classify an Instrument

```bash
curl -X POST $SERVICE_URL/tag \
  -H "Content-Type: application/json" \
  -d '{
    "instruments": [
      {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "instrument_type": "etf"
      }
    ]
  }'
```

Expected response (truncated):
```json
{
  "tagged": 1,
  "updated": ["VTI"],
  "errors": [],
  "classifications": [
    {
      "symbol": "VTI",
      "name": "Vanguard Total Stock Market ETF",
      "type": "etf",
      "current_price": 275.50,
      "asset_class": {"equity": 100.0},
      "regions": {"north_america": 100.0},
      "sectors": {
        "technology": 30.0,
        "healthcare": 15.0,
        ...
      }
    }
  ]
}
```

### 3. Verify Database Update

```bash
# Connect to Cloud SQL
gcloud sql connect alex-demo-db --user=alex_admin --database=alex

# Query the instrument
SELECT symbol, name, current_price, allocation_asset_class
FROM instruments
WHERE symbol = 'VTI';
```

## Cost Estimate

| Resource | Configuration | Monthly Cost |
|----------|--------------|-------------|
| Cloud Run | 512Mi RAM, 1 vCPU, scale-to-zero | $5-10 |
| Artifact Registry | Docker image storage | <$1 |
| **Total** | | **$5-11/month** |

Notes:
- Scales to zero when not in use (no cost)
- Charged per request + instance time
- Database costs tracked in Module 5

## Monitoring

### View Logs

```bash
gcloud run services logs read tagger-agent \
  --region=us-central1 \
  --limit=50
```

### Cloud Console Logs

1. Go to: https://console.cloud.google.com/logs
2. Filter by:
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="tagger-agent"
   ```

### Metrics Dashboard

1. Go to: https://console.cloud.google.com/run
2. Click on "tagger-agent" service
3. View: Request count, latency, instance count, errors

## Troubleshooting

### Issue: Service URL returns 404

**Cause**: Service not deployed or wrong URL

**Solution**:
```bash
# Check service status
gcloud run services describe tagger-agent --region=us-central1

# Get correct URL
terraform output service_url
```

### Issue: Health check fails with database error

**Cause**: Cloud SQL connection issue or permissions

**Solution**:
```bash
# Check Cloud SQL instance is running
gcloud sql instances describe alex-demo-db

# Verify service account has cloudsql.client role
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:*compute@developer.gserviceaccount.com"
```

### Issue: Classification fails with Bedrock error

**Cause**: AWS credentials or model access

**Solution**:
1. Check AWS credentials are configured
2. Verify Bedrock model access: https://console.aws.amazon.com/bedrock
3. Check BEDROCK_MODEL_ID and BEDROCK_REGION environment variables
4. View logs: `gcloud run services logs read tagger-agent --region=us-central1`

### Issue: Container fails to start

**Cause**: Docker image issue or environment variable problem

**Solution**:
```bash
# Check logs for startup errors
gcloud run services logs read tagger-agent --region=us-central1 --limit=100

# Verify environment variables
gcloud run services describe tagger-agent \
  --region=us-central1 \
  --format='get(spec.template.spec.containers[0].env)'

# Test Docker image locally
docker run -p 8080:8080 \
  -e CLOUD_SQL_INSTANCE=... \
  -e CLOUD_SQL_PASSWORD=... \
  -e BEDROCK_MODEL_ID=... \
  YOUR_IMAGE_URI
```

### Issue: "Secret not found" error

**Cause**: Database password secret doesn't exist

**Solution**:
```bash
# Create the secret if it doesn't exist
cd terraform_GCP/5_database
terraform output db_password | gcloud secrets create alex-db-password --data-file=-

# Or get password from terraform state
cd terraform_GCP/5_database
terraform state show random_password.db_password | grep result
```

## Updating the Service

### Update Code and Redeploy

1. Make code changes in `backend/tagger_gcp/`
2. Rebuild and push image:
   ```bash
   cd backend/tagger_gcp
   python build_and_push.py
   ```
3. Redeploy with terraform:
   ```bash
   cd terraform_GCP/6_agents
   terraform apply -replace=google_cloud_run_v2_service.tagger_agent
   ```

### Update Environment Variables Only

```bash
# Edit terraform.tfvars
nano terraform.tfvars

# Apply changes
terraform apply
```

## Cleanup

To remove all resources:

```bash
terraform destroy
```

This will:
- Delete the Cloud Run service
- Remove IAM bindings
- Stop all running instances

**Note**: Docker images in Artifact Registry are NOT deleted. Remove manually if needed:

```bash
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/PROJECT/alex-gcl-docker-repo/tagger-agent:latest
```

## Security Considerations

### Production Recommendations

1. **Disable public access**:
   ```hcl
   allow_unauthenticated = false
   ```

2. **Require authentication**:
   - Use Cloud IAM for service-to-service calls
   - Or implement API key authentication in the service

3. **Use VPC Connector** (optional):
   - For private Cloud SQL access
   - Removes need for public IP on database

4. **Rotate secrets regularly**:
   - Database password
   - AWS credentials

5. **Enable audit logging**:
   - Track all API calls
   - Monitor for suspicious activity

## Next Steps

1. **Test with more instruments**: Classify multiple ETFs, stocks, bonds
2. **Monitor costs**: Check Cloud Run billing in console
3. **Integrate with frontend**: Add API calls from NextJS app
4. **Add authentication**: Secure the endpoint for production
5. **Deploy additional agents**: Reporter, Charter, Retirement (future modules)

## Files

- `main.tf` - Cloud Run service and IAM configuration
- `variables.tf` - Input variables
- `outputs.tf` - Service URL and test commands
- `providers.tf` - GCP provider configuration
- `terraform.tfvars.example` - Configuration template
- `README.md` - This file
