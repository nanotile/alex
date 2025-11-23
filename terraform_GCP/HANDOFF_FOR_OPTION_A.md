# GCP Deployment Continuation Guide (Option A)

**For Next Session:** Complete GCP multi-cloud deployment of Alex Financial Advisor

**Current Status:** Foundation complete (25%), remaining modules need implementation
**Estimated Effort:** 6-10 days of focused development
**Prerequisites:** Read `GCP_STATUS.md` first

---

## Quick Context

### What's Done
- ✅ AWS deployment: 100% complete, production-ready
- ✅ GCP Module 0 (Foundation): APIs enabled, service accounts created
- ✅ GCP Module 2 (Embeddings): Documentation only, no infrastructure

### What's Needed
- ⬜ Modules 1, 3, 4, 5, 6, 7, 8: Terraform code + backend porting

### Why Multi-Cloud?
- Learning exercise for cloud portability
- Redundancy and disaster recovery
- Compare AWS vs GCP costs and performance
- Portfolio diversification for resume

---

## Start Here: Pre-Implementation Checklist

### Before Writing Code

**1. Verify GCP Authentication**
```bash
# Check current project
gcloud config get-value project
# Should output: gen-lang-client-0259050339

# If not authenticated:
gcloud auth login
gcloud auth application-default login
gcloud config set project gen-lang-client-0259050339
```

**2. Check Current Deployments**
```bash
cd /home/kent_benson/AWS_projects/alex/terraform_GCP

# Foundation should be deployed
cd 0_foundation && terraform output

# Embeddings should be deployed
cd ../2_embeddings && terraform output
```

**3. Review AWS Reference Architecture**
```bash
# AWS terraform is your blueprint
ls -la /home/kent_benson/AWS_projects/alex/terraform/

# Each AWS module maps to a GCP module:
# AWS terraform/5_database/ → GCP terraform_GCP/5_database/
# AWS terraform/6_agents/  → GCP terraform_GCP/6_agents/
# etc.
```

**4. Decision Points**

Answer these before coding:

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Database** | AlloyDB ($150-200/mo) vs Cloud SQL ($50-100/mo) | Cloud SQL (cheaper, sufficient) |
| **Vector Storage** | Vertex AI Vector Search ($100-200/mo) vs pgvector ($0) | pgvector in AlloyDB/Cloud SQL (massive savings) |
| **Network** | VPC + Private Service Connection vs Public IP | VPC (more secure, required for AlloyDB) |
| **Budget Ceiling** | What's max acceptable monthly cost? | Set limit before starting |

**Recommended Configuration:**
- Cloud SQL PostgreSQL (not AlloyDB)
- pgvector extension (not Vertex AI Vector Search)
- **Total GCP Cost:** ~$100-150/month (vs $380-650 with premium services)

---

## Implementation Roadmap

### Phase 1: Network & Database (Days 1-2)

**Priority:** Module 1 → Module 5 (critical path)

#### Step 1.1: Module 1 - Network (2-4 hours)

**Create:** `terraform_GCP/1_network/`

Files needed:
- `main.tf` - VPC, subnets, Private Service Connection
- `variables.tf` - region, project, network name
- `outputs.tf` - VPC ID, subnet IDs
- `terraform.tfvars.example` - Template
- `README.md` - Documentation

**Reference:**
- No direct AWS equivalent (AWS doesn't need VPC for Aurora Data API)
- GCP requires Private Service Connection for AlloyDB/Cloud SQL private access

**Terraform Resources:**
```hcl
# Key resources to create
resource "google_compute_network" "vpc"
resource "google_compute_global_address" "private_ip_address"
resource "google_service_networking_connection" "private_vpc_connection"
```

**Test:**
```bash
cd 1_network
terraform init
terraform plan
terraform apply
terraform output  # Note VPC ID for Module 5
```

---

#### Step 1.2: Module 5 - Database (6-10 hours)

**Create:** `terraform_GCP/5_database/`

Files needed:
- `main.tf` - Cloud SQL instance, database, user
- `variables.tf` - instance specs, region, VPC reference
- `outputs.tf` - instance connection name, database name
- `terraform.tfvars.example`
- `README.md`

**Key Differences from AWS:**
| AWS Aurora | GCP Cloud SQL |
|------------|---------------|
| Data API (HTTP) | Cloud SQL Connector (library) |
| No VPC needed | Requires VPC + Private Service Connection |
| Serverless v2 | Standard tiers (db-f1-micro, db-n1-standard-1) |

**Terraform Resources:**
```hcl
resource "google_sql_database_instance" "alex_db" {
  name             = "alex-gcl-db"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier = "db-f1-micro"  # Start small: $7.50/month
    # OR db-n1-standard-1  # More power: $50/month

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_id  # From Module 1
    }

    backup_configuration {
      enabled = true
      start_time = "03:00"
    }
  }
}

resource "google_sql_database" "alex" {
  name     = "alex"
  instance = google_sql_database_instance.alex_db.name
}

resource "google_sql_user" "alex_user" {
  name     = "alex_admin"
  instance = google_sql_database_instance.alex_db.name
  password = random_password.db_password.result
}
```

**Schema Migration:**
```bash
# Use same schema as AWS!
# Copy from: backend/database/migrations/001_initial_schema.sql

# Apply with psql or Cloud SQL proxy
gcloud sql connect alex-gcl-db --user=alex_admin --database=alex

# Then paste SQL schema
```

**Create Shared Library:**
`backend/database_gcp/connector.py`:
```python
from google.cloud.sql.connector import Connector
import sqlalchemy
import os

def get_connection():
    """Get Cloud SQL connection using connector"""
    connector = Connector()

    def getconn():
        conn = connector.connect(
            os.getenv("CLOUD_SQL_INSTANCE"),  # "project:region:instance"
            "pg8000",
            user=os.getenv("CLOUD_SQL_USER"),
            password=os.getenv("CLOUD_SQL_PASSWORD"),
            db=os.getenv("CLOUD_SQL_DATABASE")
        )
        return conn

    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return pool

# Usage in Cloud Run services:
# engine = get_connection()
# with engine.connect() as conn:
#     result = conn.execute("SELECT * FROM users")
```

**Test:**
```bash
cd 5_database
terraform init && terraform apply

# Get connection details
terraform output instance_connection_name
# Example: gen-lang-client-0259050339:us-central1:alex-gcl-db

# Test connection
gcloud sql connect alex-gcl-db --user=alex_admin
```

---

### Phase 2: Backend Services (Days 3-5)

#### Step 2.1: Module 4 - Researcher (4-6 hours)

**Create:** `terraform_GCP/4_researcher/`

**Port from:** `backend/researcher/` + `terraform/4_researcher/`

**Key Changes:**
1. Dockerfile for Cloud Run (instead of App Runner)
2. Replace Bedrock with Vertex AI Gemini
3. Replace Aurora Data API with Cloud SQL connector
4. Cloud Scheduler instead of EventBridge

**main.tf:**
```hcl
# Build and push container
resource "google_artifact_registry_repository" "researcher" {
  # Use repository from Module 0
}

resource "google_cloud_run_service" "researcher" {
  name     = "alex-gcl-researcher"
  location = var.gcp_region

  template {
    spec {
      service_account_name = var.service_account_email

      containers {
        image = "${var.artifact_registry_url}/researcher:latest"

        env {
          name  = "GCP_PROJECT"
          value = var.gcp_project
        }
        env {
          name  = "CLOUD_SQL_INSTANCE"
          value = var.cloud_sql_instance
        }
        env {
          name = "VERTEX_AI_MODEL"
          value = "gemini-1.5-pro"
        }
      }
    }
  }
}

# Cloud Scheduler for periodic execution
resource "google_cloud_scheduler_job" "researcher_trigger" {
  name     = "researcher-daily"
  schedule = "0 9 * * *"  # 9 AM daily

  http_target {
    uri         = google_cloud_run_service.researcher.status[0].url
    http_method = "POST"

    oidc_token {
      service_account_email = var.scheduler_sa_email
    }
  }
}
```

**Code Changes (`backend/researcher/server.py`):**
```python
# OLD (AWS):
from litellm import completion
response = completion(
    model="bedrock/us.amazon.nova-pro-v1:0",
    messages=messages
)

# NEW (GCP):
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project=os.getenv("GCP_PROJECT"), location="us-central1")
model = GenerativeModel("gemini-1.5-pro")
response = model.generate_content(messages)
```

---

#### Step 2.2: Module 3 - Ingestion (6-8 hours)

**Port from:** `backend/ingest/` + `terraform/3_ingestion/`

**Decision Point:** Vector storage strategy

**Option A: Vertex AI Vector Search (Premium)**
- Cost: $100-200/month
- Managed service
- Better for high-scale production

**Option B: pgvector in Cloud SQL (Budget)**
- Cost: $0 (included in Cloud SQL)
- Manual index management
- Good for learning/development

**Recommended: Option B (pgvector)**

**Setup pgvector:**
```sql
-- In Cloud SQL database
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),  -- 768 dimensions for Vertex AI
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
```

**Cloud Run Service:**
```hcl
resource "google_cloud_run_service" "ingest" {
  name     = "alex-gcl-ingest"
  location = var.gcp_region

  template {
    spec {
      containers {
        image = "${var.artifact_registry_url}/ingest:latest"

        env {
          name  = "VERTEX_EMBEDDING_MODEL"
          value = "text-embedding-004"
        }
        env {
          name  = "CLOUD_SQL_INSTANCE"
          value = var.cloud_sql_instance
        }
      }
    }
  }
}

# API Gateway or direct Cloud Run URL
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.ingest.name
  location = google_cloud_run_service.ingest.location
  role     = "roles/run.invoker"
  member   = "allUsers"  # Or restrict with API key
}
```

---

#### Step 2.3: Module 6 - Agents (10-16 hours) **LARGEST MODULE**

**Port from:** `backend/planner/`, `backend/tagger/`, `backend/reporter/`, `backend/charter/`, `backend/retirement/` + `terraform/6_agents/`

**Architectural Change:** SQS (pull) → Cloud Tasks (push)

**AWS Pattern:**
```
API → SQS → Lambda polls → Planner invokes other Lambdas
```

**GCP Pattern:**
```
API → Cloud Tasks → Planner HTTP endpoint → Planner POSTs to agent endpoints
```

**main.tf (5 Cloud Run services):**
```hcl
# Repeat for: planner, tagger, reporter, charter, retirement
resource "google_cloud_run_service" "planner" {
  name     = "alex-gcl-planner"
  location = var.gcp_region

  template {
    spec {
      containers {
        image = "${var.artifact_registry_url}/planner:latest"

        env {
          name  = "VERTEX_AI_MODEL"
          value = "gemini-1.5-pro"
        }
        env {
          name  = "TAGGER_URL"
          value = google_cloud_run_service.tagger.status[0].url
        }
        env {
          name  = "REPORTER_URL"
          value = google_cloud_run_service.reporter.status[0].url
        }
        # ... other agent URLs
      }
    }
  }
}

# Cloud Tasks queue
resource "google_cloud_tasks_queue" "analysis_jobs" {
  name     = "alex-gcl-analysis-jobs"
  location = var.gcp_region
}
```

**Code Changes (Planner invocation):**
```python
# OLD (AWS Lambda):
import boto3
lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='alex-reporter',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

# NEW (GCP Cloud Run):
import requests
import google.auth.transport.requests
from google.oauth2 import service_account

# Get Cloud Run URL from environment
reporter_url = os.getenv("REPORTER_URL")

# Make authenticated HTTP request
response = requests.post(
    reporter_url,
    json=payload,
    headers={"Authorization": f"Bearer {get_id_token()}"}
)
```

---

### Phase 3: Frontend & Monitoring (Days 6-8)

#### Step 3.1: Module 7 - Frontend (8-12 hours)

**Port from:** `frontend/` + `terraform/7_frontend/`

**Components:**
1. Cloud Storage bucket (static site)
2. Cloud CDN
3. Cloud Run API service
4. Load Balancer

**main.tf:**
```hcl
# Static frontend bucket
resource "google_storage_bucket" "frontend" {
  name     = "${var.project_name}-frontend"
  location = var.gcp_region

  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }
}

# Cloud CDN
resource "google_compute_backend_bucket" "frontend_backend" {
  name        = "${var.project_name}-backend"
  bucket_name = google_storage_bucket.frontend.name
  enable_cdn  = true
}

# API service
resource "google_cloud_run_service" "api" {
  name     = "alex-gcl-api"
  location = var.gcp_region

  template {
    spec {
      containers {
        image = "${var.artifact_registry_url}/api:latest"

        env {
          name  = "CLERK_JWKS_URL"
          value = var.clerk_jwks_url
        }
        env {
          name  = "CLOUD_SQL_INSTANCE"
          value = var.cloud_sql_instance
        }
      }
    }
  }
}
```

**Frontend Build:**
```bash
cd frontend

# Update .env.production.local with GCP API URL
NEXT_PUBLIC_API_URL=https://alex-gcl-api-xxxx.run.app

# Build
npm run build

# Upload to Cloud Storage
gsutil -m rsync -r out/ gs://alex-gcl-frontend/
```

---

#### Step 3.2: Module 8 - Monitoring (3-5 hours)

**Port from:** `terraform/8_enterprise/`

**Cloud Monitoring Dashboards:**
```hcl
resource "google_monitoring_dashboard" "agent_performance" {
  dashboard_json = jsonencode({
    displayName = "Alex GCP - Agent Performance"

    widgets = [
      {
        title = "Cloud Run Request Count"
        xyChart = {
          dataSets = [{
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
              }
            }
          }]
        }
      },
      {
        title = "Cloud Run Response Latency"
        xyChart = {
          dataSets = [{
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
              }
            }
          }]
        }
      }
    ]
  })
}

# Alert policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "Alex - High Error Rate"

  conditions {
    display_name = "Error rate > 5%"

    condition_threshold {
      filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""

      threshold_value = 5.0
      comparison      = "COMPARISON_GT"
    }
  }
}
```

---

## Testing Strategy

### Local Testing (Before Deployment)

```bash
# Test Cloud SQL connector
cd backend/database_gcp
uv run test_connector.py

# Test Vertex AI Gemini
cd backend
uv run test_vertex_gemini.py

# Test each agent locally with mocks
cd backend/planner && uv run test_simple.py
cd ../reporter && uv run test_simple.py
# ... etc
```

### Integration Testing (After Deployment)

```bash
# Test each Cloud Run service
# Planner
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://alex-gcl-planner-xxxx.run.app/health

# End-to-end test
cd backend && uv run test_gcp_full.py
```

---

## Deployment Workflow

### Per Module
```bash
cd terraform_GCP/X_module

# 1. Write terraform code
# 2. Copy tfvars example
cp terraform.tfvars.example terraform.tfvars

# 3. Edit variables
nano terraform.tfvars

# 4. Deploy
terraform init
terraform plan
terraform apply

# 5. Note outputs for next module
terraform output
```

### Container Build & Deploy
```bash
# Build for Cloud Run
cd backend/planner

docker build -t us-central1-docker.pkg.dev/gen-lang-client-0259050339/alex-gcl-docker-repo/planner:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/gen-lang-client-0259050339/alex-gcl-docker-repo/planner:latest

# Deploy Cloud Run service (via terraform)
cd ../../terraform_GCP/6_agents
terraform apply
```

---

## Common Pitfalls & Solutions

### Pitfall 1: VPC Connectivity
**Problem:** Cloud Run can't connect to Cloud SQL
**Solution:** Ensure Private Service Connection is established in Module 1

### Pitfall 2: Authentication Errors
**Problem:** 403 errors when calling Cloud Run services
**Solution:** Use proper IAM service account authentication

### Pitfall 3: Vector Dimension Mismatch
**Problem:** Trying to use AWS embeddings (384) with GCP (768)
**Solution:** Re-embed all documents with Vertex AI

### Pitfall 4: Bedrock → Gemini Prompt Differences
**Problem:** Prompts don't work the same on Gemini
**Solution:** Test and tune each agent's prompts for Gemini

### Pitfall 5: Database Connection Pooling
**Problem:** Cloud Run instances exhaust connections
**Solution:** Use Cloud SQL connector's built-in pooling

---

## Cost Monitoring During Development

```bash
# Check current GCP costs
gcloud billing accounts list

gcloud billing projects describe gen-lang-client-0259050339

# Set budget alert
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="Alex GCP Budget" \
  --budget-amount=200 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100
```

---

## When to Stop and Re-evaluate

**Red Flags:**
- [ ] GCP costs exceed $200/month
- [ ] Implementation taking > 2 weeks
- [ ] AWS version is sufficient for project needs
- [ ] Budget constraints

**Decision Point:**
If GCP is primarily for learning, consider:
- Implement only 1-2 modules (e.g., database + 1 agent)
- Document architectural differences
- Keep AWS as primary deployment

---

## Success Criteria

**Minimum Viable GCP Deployment:**
- [ ] Module 1: Network deployed
- [ ] Module 5: Database deployed + schema migrated
- [ ] Module 6: At least 1 agent working (start with Tagger)
- [ ] Can invoke agent via HTTP and get response
- [ ] Database queries work via Cloud SQL connector

**Full GCP Deployment:**
- [ ] All 8 modules deployed
- [ ] Frontend accessible via Cloud CDN
- [ ] Full analysis workflow works end-to-end
- [ ] Costs < $200/month
- [ ] CloudMonitoring dashboards showing metrics

---

## Estimated Timeline

| Phase | Modules | Days | Hours |
|-------|---------|------|-------|
| **Phase 1** | 1, 5 | 2 | 12-16 |
| **Phase 2** | 3, 4, 6 | 3 | 20-30 |
| **Phase 3** | 7, 8 | 2 | 12-18 |
| **Testing & Debug** | All | 1 | 8-12 |
| **Total** | **1-8** | **8-10** | **52-76** |

**Realistic Estimate:** 10 full days or 2-3 weeks part-time

---

## Next Session Startup Commands

```bash
# Navigate to GCP terraform
cd /home/kent_benson/AWS_projects/alex/terraform_GCP

# Verify authentication
gcloud auth list
gcloud config get-value project

# Check what's deployed
ls -la */terraform.tfstate

# Review status
cat GCP_STATUS.md

# Start with Module 1
cd 1_network
# Create main.tf, variables.tf, outputs.tf...
```

---

## Resources

**Documentation:**
- `terraform_GCP/GCP_STATUS.md` - Current state
- `terraform_GCP/README_GCP.md` - Architecture overview
- `terraform/` - AWS reference implementation

**GCP Docs:**
- Cloud Run: https://cloud.google.com/run/docs
- Cloud SQL: https://cloud.google.com/sql/docs
- Vertex AI: https://cloud.google.com/vertex-ai/docs

**Tools:**
- Terraform GCP Provider: https://registry.terraform.io/providers/hashicorp/google/latest/docs
- gcloud CLI Reference: https://cloud.google.com/sdk/gcloud/reference

---

**Good Luck! Start with Module 1 (Network) → Module 5 (Database) → then the rest.**

**Remember:** The goal is learning, not perfection. Get 1 agent working end-to-end, then expand.
