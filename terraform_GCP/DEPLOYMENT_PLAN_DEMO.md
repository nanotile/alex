# GCP Deployment Plan - Learning/Demo Mode

**Goal:** Demonstrate multi-cloud capability with minimal cost (~$50-100/month)
**Strategy:** Deploy only essential components to show architectural portability
**Date:** November 23, 2025

---

## What We'll Deploy (Minimal Viable Demo)

### ✅ Already Deployed
- **Module 0:** Foundation (APIs, service accounts) - $0/month
- **Module 2:** Embeddings (Vertex AI config) - Pay-per-use only

### 🎯 To Deploy for Demo
- **Module 5:** Database (Cloud SQL minimal tier) - ~$25-40/month
- **Module 6:** One Agent (Tagger on Cloud Run) - ~$5-10/month

### ⏭️ Skip for Now (Not Needed for Demo)
- **Module 1:** Network (use default VPC) - $0
- **Module 3:** Ingestion (not critical for demo)
- **Module 4:** Researcher (already have AWS version)
- **Module 6:** Other 4 agents (Tagger is sufficient to prove concept)
- **Module 7:** Frontend (AWS frontend can call GCP API)
- **Module 8:** Monitoring (use basic GCP Cloud Monitoring UI)

---

## Cost Breakdown (Demo Configuration)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **Cloud SQL** | db-f1-micro (shared CPU, 0.6GB RAM) | $25-40 |
| **Cloud Run** | 1 service (Tagger), pay-per-use | $5-10 |
| **Vertex AI Embeddings** | Pay-per-use (minimal) | $1-5 |
| **Cloud Storage** | Minimal usage | $1-2 |
| **Networking** | Egress (minimal) | $2-5 |
| **TOTAL** | | **$34-62/month** |

**Compare to:**
- Full GCP deployment: $380-650/month
- Current AWS: $50-75/month

---

## Architecture (Demo Mode)

```
                    ┌──────────────┐
                    │  AWS (Prod)  │
                    │  Frontend    │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌────────┐      ┌────────┐       ┌────────┐
    │  AWS   │      │  GCP   │       │  AWS   │
    │Planner │──────│Tagger  │───────│Database│
    │Lambda  │      │Cloud   │       │Aurora  │
    └────────┘      │  Run   │       └────────┘
                    └────┬───┘
                         │
                         ▼
                    ┌────────┐
                    │  GCP   │
                    │Cloud   │
                    │  SQL   │
                    └────────┘
```

**What this demonstrates:**
- ✅ Multi-cloud architecture
- ✅ Agent portability (same code, different cloud)
- ✅ Cross-cloud communication
- ✅ Database migration capability
- ✅ Cost-conscious deployment

---

## Implementation Steps

### Step 1: Deploy Cloud SQL (Minimal Configuration)

**Location:** `terraform_GCP/5_database/`

**Configuration:**
- Instance tier: `db-f1-micro` (shared CPU, 0.6GB RAM)
- No high availability (saves 50%)
- No read replicas
- Minimal storage (10GB)
- Public IP (no Private Service Connection needed - simpler!)
- Daily backup only

**Terraform code:**
```hcl
resource "google_sql_database_instance" "alex_demo" {
  name             = "alex-demo-db"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier = "db-f1-micro"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = true  # Public IP - simpler for demo
      authorized_networks {
        name  = "Allow Cloud Run"
        value = "0.0.0.0/0"  # Will restrict after testing
      }
    }
  }

  deletion_protection = false  # For easy cleanup
}
```

**Cost:** ~$25-40/month (1/4 the cost of AlloyDB)

---

### Step 2: Deploy Tagger Agent on Cloud Run

**Location:** `terraform_GCP/6_agents/`

**Why Tagger?**
- Simplest agent (no external API calls)
- Pure classification logic
- Easy to test
- Proves the portability concept

**Configuration:**
- Memory: 512MB (minimal)
- CPU: 1 (minimal)
- Concurrency: 10
- Min instances: 0 (scale to zero)
- Max instances: 2

**Code changes needed:**
```python
# OLD (AWS):
from database import Database  # Aurora Data API
db = Database()

# NEW (GCP):
from google.cloud.sql.connector import Connector
import sqlalchemy

connector = Connector()
def getconn():
    return connector.connect(
        os.getenv("CLOUD_SQL_INSTANCE"),
        "pg8000",
        user=os.getenv("CLOUD_SQL_USER"),
        password=os.getenv("CLOUD_SQL_PASSWORD"),
        db="alex"
    )

engine = sqlalchemy.create_engine("postgresql+pg8000://", creator=getconn)
```

**Cost:** ~$5-10/month (pay-per-use)

---

### Step 3: Test End-to-End

**Test Flow:**
1. Insert test data into GCP Cloud SQL
2. Call Tagger Cloud Run endpoint
3. Verify classification results
4. Check database updates

**Success Criteria:**
- ✅ Agent can connect to Cloud SQL
- ✅ Agent processes requests correctly
- ✅ Results match AWS behavior
- ✅ Cost stays under $100/month

---

## What This Proves

### For Resume/Portfolio:
- **Multi-cloud architecture design** - Demonstrated
- **Cloud-agnostic application development** - Proven
- **AWS to GCP migration** - Showcased
- **Cost optimization** - Documented
- **Infrastructure as Code** - Both clouds

### Technical Skills Demonstrated:
- ✅ Cloud SQL (GCP's managed PostgreSQL)
- ✅ Cloud Run (GCP's serverless containers)
- ✅ Vertex AI (GCP's AI platform)
- ✅ Cross-cloud networking
- ✅ Database migration strategies
- ✅ Cost analysis and optimization

---

## Timeline

**Estimated Effort:** 4-6 hours

| Task | Time | Complexity |
|------|------|------------|
| Cloud SQL deployment | 1-2 hours | Medium |
| Database schema migration | 30 min | Low |
| Tagger agent porting | 2-3 hours | Medium |
| Testing & debugging | 1-2 hours | Medium |
| Documentation | 30 min | Low |

**Total:** Half a day to full day

---

## Future Expansion (Optional)

If you want to expand later:

**Phase 2 (add $20-30/month):**
- Add Reporter agent
- Deploy Ingestion service

**Phase 3 (add $30-50/month):**
- Add remaining agents
- Deploy frontend to Cloud Storage + CDN

**Phase 4 (add $100-200/month):**
- Upgrade to Cloud SQL Standard tier
- Add high availability
- Implement full monitoring

---

## Cleanup Strategy

To keep costs minimal when not actively using:

**Option 1: Pause (keep infrastructure, stop database)**
```bash
gcloud sql instances patch alex-demo-db --activation-policy=NEVER
# Cost: $0/month storage only (~$2/month)
```

**Option 2: Destroy Everything**
```bash
cd terraform_GCP/6_agents && terraform destroy
cd ../5_database && terraform destroy
# Cost: $0/month
```

**Option 3: Keep Running**
- Cost: ~$34-62/month
- Always ready for demos

---

## Decision Matrix

| Aspect | Full Deployment | Demo Deployment (This Plan) |
|--------|----------------|----------------------------|
| **Cost** | $380-650/mo | $34-62/mo |
| **Time to Deploy** | 6-10 days | 4-6 hours |
| **Components** | All 8 modules | 2 modules |
| **Resume Value** | High | Medium-High |
| **Learning Value** | High | High |
| **Maintenance** | Complex | Simple |
| **Proof of Concept** | Complete | Sufficient |

---

## Next Steps

1. **Review this plan** - Make sure it aligns with your goals
2. **Deploy Cloud SQL** - Start with database
3. **Port Tagger agent** - One agent is enough to prove concept
4. **Test & document** - Show it works
5. **Add to portfolio** - Demonstrate multi-cloud capability

---

## Questions Before Starting

- [ ] Does this cost level ($34-62/month) work for you?
- [ ] Is Tagger agent sufficient, or do you want Reporter instead?
- [ ] Do you want to keep this running long-term or just for demos?
- [ ] Should we restrict Cloud SQL to specific IPs or leave public for simplicity?

---

**Recommendation:** Start with this minimal deployment. It proves the concept, keeps costs low, and you can always expand later if needed.

**Total GCP Cost After This:** $34-62/month
**Combined AWS + GCP:** $84-137/month
**Learning/Demo Value:** High
**Resume Impact:** Demonstrates multi-cloud architecture skills

---

Ready to proceed?
