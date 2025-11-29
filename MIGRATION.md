# Alex Repository Split - Migration Guide

**Date**: November 2025
**Version**: 2.0.0

## Overview

The Alex project has been split from a single multi-cloud repository into two independent repositories:

- **alex** (this repository): AWS-only deployment
- **alex-gcp** (new repository): GCP-only deployment

## What Changed

### Repository Structure

**Before** (Multi-Cloud):
```
alex/
├── backend/
│   ├── database/          # AWS Aurora library
│   ├── database_gcp/      # GCP Cloud SQL library
│   ├── tagger/            # AWS Lambda agent
│   ├── tagger_gcp/        # GCP Cloud Run agent
│   └── ...
├── terraform/             # AWS infrastructure
├── terraform_GCP/         # GCP infrastructure
├── scripts/
│   ├── deploy_multi_cloud.py
│   └── destroy_multi_cloud.py
└── ...
```

**After** (AWS-Only):
```
alex/
├── backend/
│   ├── database/          # AWS Aurora library
│   ├── tagger/            # AWS Lambda agent
│   └── ...
├── terraform/             # AWS infrastructure
├── scripts/
│   └── AWS_START_STOP/    # AWS cost management
└── ...
```

### Deleted from alex Repository

The following GCP-specific code has been removed:

**Backend:**
- `backend/database_gcp/` - GCP Cloud SQL client library
- `backend/tagger_gcp/` - GCP Cloud Run version of tagger agent

**Infrastructure:**
- `terraform_GCP/` - All GCP terraform configurations
  - `0_foundation/` - GCP project setup
  - `1_network/` - VPC and networking
  - `2_embeddings/` - Vertex AI embeddings
  - `3_ingestion/` - Cloud Storage + Functions
  - `4_researcher/` - Cloud Run service
  - `5_database/` - Cloud SQL
  - `6_agents/` - Cloud Run agents
  - `7_frontend/` - Cloud CDN + Storage
  - `8_monitoring/` - Cloud Monitoring

**Scripts:**
- `scripts/deploy_multi_cloud.py` - Multi-cloud deployment script
- `scripts/destroy_multi_cloud.py` - Multi-cloud cleanup script
- `scripts/AWS_START_STOP/deploy_multi_cloud.py` - Removed from cost management

### Preserved in Archive

All deleted code is preserved in the `archive/multi-cloud-final` branch for reference.

## Migration Paths

### If You're Using AWS (Current Repository)

**No action required!** Continue using this repository:

```bash
# Your existing workflow remains the same
cd terraform/5_database
terraform apply

cd backend/tagger
uv run pytest test_full.py
```

**What's New:**
- Cleaner codebase (no GCP references)
- Updated documentation (AWS-specific)
- Same deployment guides (1-8)
- Same agent architecture

### If You're Using GCP

**Switch to the alex-gcp repository:**

```bash
# Clone the new GCP repository
git clone https://github.com/your-org/alex-gcp.git
cd alex-gcp

# Follow the GCP-specific guides (0-8)
# Guide 0: GCP Foundation
# Guide 1: Network Setup
# Guides 2-8: Similar to AWS but GCP-specific
```

### If You're Using Both Clouds

**Maintain both repositories separately:**

```bash
# AWS deployment
cd ~/projects/alex-aws
git pull
# Follow AWS guides 2-8

# GCP deployment
cd ~/projects/alex-gcp
git pull
# Follow GCP guides 0-8
```

## Why We Split the Repository

### Rationale

1. **Clarity**: Each repository focuses on one cloud provider
2. **Simplicity**: No more multi-cloud complexity for single-cloud users
3. **Independence**: Each team can evolve their stack independently
4. **Maintenance**: Easier to maintain cloud-specific code
5. **Learning**: Clear separation for students learning one cloud at a time

### Trade-offs

**Benefits:**
- Simpler codebase per repository
- No confusion about which cloud you're using
- Easier for beginners to follow guides
- Each repo is self-contained

**Considerations:**
- Agent improvements must be synced manually between repos
- Frontend updates need to be duplicated
- Shared testing utilities duplicated
- Two repos to maintain instead of one

## What Stays the Same

Both repositories share:

1. **Agent Logic**: `agent.py` and `templates.py` are identical
2. **Frontend**: 100% cloud-agnostic NextJS application
3. **Testing Framework**: Same test structure and patterns
4. **Git Utilities**: Shared helper scripts in `KB_github_UTILITIES/`
5. **OpenAI Agents SDK**: Same framework for all agents

## Repository URLs

- **AWS Version** (this repo): `https://github.com/your-org/alex`
- **GCP Version**: `https://github.com/your-org/alex-gcp`
- **Archive Branch**: `archive/multi-cloud-final` in this repo

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.x.x | Oct 2025 | Multi-cloud version (AWS + GCP) |
| 2.0.0 | Nov 2025 | **Repository split** - AWS-only version |

## Support

### For AWS Users

Continue using this repository. All guides (1-8) work as before.

**Resources:**
- AWS-specific guides in `guides/`
- AWS cost management in `scripts/AWS_START_STOP/`
- AWS architecture documented in README.md

### For GCP Users

Switch to the alex-gcp repository.

**Resources:**
- GCP-specific guides (0-8) in new repository
- GCP deployment scripts
- GCP architecture documented in README.md

### Questions?

- **AWS Issues**: Open issues in this repository
- **GCP Issues**: Open issues in alex-gcp repository
- **General Questions**: Email ed@edwarddonner.com

## Frequently Asked Questions

### Q: Will agent improvements be synced between repos?

A: Agent logic (`agent.py`, `templates.py`) is identical initially. Future improvements should be manually synced or contributed to both repos.

### Q: What about the frontend?

A: The frontend is 100% identical in both repos (fully cloud-agnostic).

### Q: Can I still see the multi-cloud code?

A: Yes! It's preserved in the `archive/multi-cloud-final` branch:

```bash
git checkout archive/multi-cloud-final
# View the original multi-cloud implementation
```

### Q: Do I need to redeploy?

A: **No** if you're already deployed on AWS. The infrastructure hasn't changed, just the repository structure.

### Q: What if I want multi-cloud support?

A: Deploy both repositories side-by-side. They're completely independent and won't conflict.

## Technical Details

### Entry Points

**AWS (Lambda):**
```python
# lambda_handler.py
def lambda_handler(event, context):
    # AWS Lambda entry point
    pass
```

**GCP (Cloud Run):**
```python
# main.py
from fastapi import FastAPI
app = FastAPI()

@app.post("/invoke")
async def invoke_agent(request):
    # GCP Cloud Run entry point
    pass
```

### Database Libraries

**AWS:**
```python
from backend.database import DatabaseClient

db = DatabaseClient(
    cluster_arn=os.getenv("AURORA_CLUSTER_ARN"),
    secret_arn=os.getenv("AURORA_SECRET_ARN"),
    database=os.getenv("AURORA_DATABASE")
)
```

**GCP:**
```python
from backend.database import CloudSQLClient

db = CloudSQLClient(
    instance=os.getenv("CLOUD_SQL_INSTANCE"),
    user=os.getenv("CLOUD_SQL_USER"),
    password=os.getenv("CLOUD_SQL_PASSWORD"),
    database=os.getenv("CLOUD_SQL_DATABASE")
)
```

## Next Steps

1. **Choose your cloud**: AWS (this repo) or GCP (alex-gcp)
2. **Follow the guides**: Guides 2-8 for AWS, Guides 0-8 for GCP
3. **Deploy incrementally**: One terraform module at a time
4. **Test thoroughly**: Use both `test_simple.py` and `test_full.py`
5. **Monitor costs**: Use cost management scripts

---

*This migration guide is for reference only. No action is required for existing AWS deployments.*

For the latest updates, see the `CHANGELOG.md` in each repository.
