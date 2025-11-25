# Tagger Agent - GCP Cloud Run

Financial instrument classification agent deployed on Google Cloud Run.

## Overview

The Tagger Agent classifies financial instruments (ETFs, stocks, bonds) and provides detailed allocation breakdowns:
- **Asset classes**: equity, fixed income, real estate, commodities, cash, alternatives
- **Regions**: North America, Europe, Asia, etc.
- **Sectors**: Technology, healthcare, financials, etc.

## Architecture

- **Runtime**: Cloud Run (serverless containers)
- **API**: FastAPI (REST endpoints)
- **AI**: AWS Bedrock (Nova Pro model via LiteLLM)
- **Database**: Cloud SQL (via database_gcp library)

## API Endpoints

### `GET /`
Health check - returns service info

### `GET /health`
Detailed health check - tests database connection

### `POST /tag`
Classify instruments and update database

Request body:
```json
{
  "instruments": [
    {
      "symbol": "SPY",
      "name": "SPDR S&P 500 ETF Trust",
      "instrument_type": "etf"
    }
  ]
}
```

Response:
```json
{
  "tagged": 1,
  "updated": ["SPY"],
  "errors": [],
  "classifications": [
    {
      "symbol": "SPY",
      "name": "SPDR S&P 500 ETF Trust",
      "type": "etf",
      "current_price": 450.25,
      "asset_class": {"equity": 100.0},
      "regions": {"north_america": 100.0},
      "sectors": {
        "technology": 30.0,
        "healthcare": 15.0,
        "financials": 12.0,
        ...
      }
    }
  ]
}
```

## Environment Variables

```bash
# AWS Bedrock (for AI classification)
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
BEDROCK_REGION=us-west-2
AWS_REGION_NAME=us-west-2

# GCP Cloud SQL
CLOUD_SQL_INSTANCE=project:region:instance
CLOUD_SQL_DATABASE=alex
CLOUD_SQL_USER=alex_admin
CLOUD_SQL_PASSWORD=your-password

# Server
PORT=8080
```

## Local Development

1. **Install dependencies**:
```bash
cd backend/tagger_gcp
uv venv
uv pip install -e ../database_gcp
uv pip install -r pyproject.toml
```

2. **Set environment variables**:
```bash
cp .env.example .env
# Edit .env with your values
```

3. **Run locally**:
```bash
uv run python main.py
```

4. **Test endpoint**:
```bash
curl http://localhost:8080/health
```

## Deployment

### 1. Build and push Docker image

```bash
# Using the build script
python build_and_push.py

# Or manually
cd backend
docker build -t us-central1-docker.pkg.dev/PROJECT/REPO/tagger-agent:latest -f tagger_gcp/Dockerfile .
docker push us-central1-docker.pkg.dev/PROJECT/REPO/tagger-agent:latest
```

### 2. Deploy with Terraform

```bash
cd terraform_GCP/6_agents
terraform init
terraform apply
```

### 3. Test deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe tagger-agent --region=us-central1 --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test classification
curl -X POST $SERVICE_URL/tag \
  -H "Content-Type: application/json" \
  -d '{
    "instruments": [
      {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "instrument_type": "etf"}
    ]
  }'
```

## Differences from AWS Lambda Version

| Aspect | AWS Lambda | GCP Cloud Run |
|--------|-----------|---------------|
| **Runtime** | Lambda function | Container (FastAPI) |
| **API** | Lambda event/context | HTTP REST endpoints |
| **Database** | Aurora Data API | Cloud SQL Connector |
| **Deployment** | ZIP file / Docker | Docker only |
| **Scaling** | Automatic (per request) | Automatic (container instances) |
| **Cold start** | ~1-2 seconds | ~2-3 seconds |
| **Timeout** | 15 minutes max | 60 minutes max |
| **Cost** | Per invocation | Per request + instance time |

## Cost Estimate

- **Cloud Run**: ~$5-10/month (minimal usage)
- **Container Registry**: <$1/month
- **Total**: $5-11/month

(Database costs tracked separately in `terraform_GCP/5_database`)

## Monitoring

View logs in GCP Console:
```bash
gcloud run services logs read tagger-agent --region=us-central1 --limit=50
```

Or use Cloud Logging:
- Go to: https://console.cloud.google.com/logs
- Filter: `resource.type="cloud_run_revision" AND resource.labels.service_name="tagger-agent"`

## Troubleshooting

### Issue: Container fails to start
- Check logs: `gcloud run services logs read tagger-agent --region=us-central1`
- Verify environment variables are set in Cloud Run
- Test database connectivity from Cloud Shell

### Issue: Classification fails
- Check Bedrock model access in AWS console
- Verify AWS credentials are available
- Check model ID matches available model

### Issue: Database connection fails
- Verify CLOUD_SQL_INSTANCE format: `project:region:instance`
- Check Cloud SQL instance is running
- Verify password in Secret Manager or terraform state
- Ensure Cloud Run service account has Cloud SQL Client role

## Files

- `main.py` - FastAPI server and endpoints
- `agent.py` - Classification logic (OpenAI Agents SDK)
- `schemas.py` - Pydantic models
- `templates.py` - AI prompts
- `Dockerfile` - Container build configuration
- `build_and_push.py` - Deployment script
- `pyproject.toml` - Python dependencies
