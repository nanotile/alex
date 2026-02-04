# Alex Application State — February 4, 2026

## What Alex Is

Alex (Agentic Learning Equities eXplainer) is a multi-agent SaaS financial planning platform deployed on AWS. It analyzes investment portfolios, generates reports with charts, runs retirement projections via Monte Carlo simulation, and autonomously researches market trends. Built as a capstone for Ed Donner's "AI in Production" Udemy course (Weeks 3-4), following 8 incremental deployment guides in `guides/`.

---

## How It Works (End-to-End Flow)

```
User (browser)
  → Next.js frontend (Clerk auth, CloudFront CDN)
    → FastAPI API (Lambda via API Gateway)
      → SQS job queue
        → Planner agent (Lambda) — orchestrator
            ├→ Tagger agent    — classifies instruments by asset class/region/sector
            ├→ Reporter agent  — portfolio analysis + market context from S3 Vectors
            ├→ Charter agent   — generates interactive chart data
            └→ Retirement agent — Monte Carlo retirement projections (1000+ scenarios)

Researcher agent (App Runner, every 2 hours)
  → scrapes financial sites with Playwright
  → embeds via SageMaker (all-MiniLM-L6-v2)
  → stores in S3 Vectors knowledge base
  → Reporter queries this context during analysis

All AI agents use AWS Bedrock Nova Pro via LiteLLM + OpenAI Agents SDK
All agents share Aurora PostgreSQL (Data API) via the alex-database package
```

---

## Infrastructure Map

| Module | What It Deploys | Monthly Cost | Current Status |
|--------|----------------|-------------|----------------|
| **2_sagemaker** | SageMaker serverless embedding endpoint (all-MiniLM-L6-v2, 3GB) | ~$10 | Likely deployed |
| **3_ingestion** | S3 Vectors bucket + Lambda ingestion + API Gateway (key auth, rate limited) | ~$1-5 | Likely deployed |
| **4_researcher** | ECR repo + App Runner service (1 vCPU, 2GB) for autonomous research | ~$51 | **Destroyed** (cost savings) |
| **5_database** | Aurora Serverless v2 PostgreSQL 15.12 + Secrets Manager (Data API) | ~$65 | **Destroyed** (cost savings) |
| **6_agents** | 5 Lambda functions + SQS queue + DLQ + IAM roles + CloudWatch logs | ~$1 | Likely deployed |
| **7_frontend** | CloudFront + S3 static site + API Gateway Lambda proxy | ~$2 | Likely deployed |
| **8_enterprise** | 2 CloudWatch dashboards | ~$5 | Likely deployed |

**Last recorded state** (`scripts/.last_state.json`): Dec 18, 2025 — modules `4_researcher` and `5_database` destroyed to minimize costs.

**Estimated running cost**: ~$19/month (without Aurora & Researcher). Full deployment: ~$135/month.

Each Terraform module is independent with local state. No remote backend.

---

## Database Schema (Aurora PostgreSQL)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **users** | User profiles | clerk_user_id (PK), display_name, years_until_retirement, target_retirement_income, asset_class_targets (JSONB), region_targets (JSONB) |
| **instruments** | Financial reference data | symbol (PK), name, instrument_type, current_price, allocation by region/sector/asset_class (JSONB) |
| **accounts** | Portfolio accounts | id (UUID), clerk_user_id (FK), account_name, account_purpose, cash_balance |
| **positions** | Holdings per account | id (UUID), account_id (FK), symbol (FK), quantity (DECIMAL 20,8), as_of_date. Unique on (account_id, symbol) |
| **jobs** | Analysis job tracking | id (UUID), clerk_user_id (FK), status (pending/running/completed/failed), report_payload, charts_payload, retirement_payload, summary_payload (all JSONB) |

---

## Backend Agents (each is a uv project under `backend/`)

| Agent | Runtime | Role |
|-------|---------|------|
| **api** | Lambda (FastAPI + Mangum) | REST API for frontend, Clerk auth, user/portfolio/job CRUD |
| **planner** | Lambda | Orchestrator — receives SQS jobs, dispatches specialists, aggregates results |
| **tagger** | Lambda | Classifies instruments by asset class, region, sector (structured output, no tools) |
| **reporter** | Lambda | Portfolio analysis with S3 Vectors market context (tool calling, no structured output) |
| **charter** | Lambda | Generates 4-6 chart specifications from analysis data |
| **retirement** | Lambda | Monte Carlo simulations — withdrawal modeling, survival probability |
| **researcher** | App Runner (FastAPI) | Autonomous web scraper, embeds findings into S3 Vectors |
| **ingest** | Lambda | Document vectorization via SageMaker endpoint into S3 Vectors |
| **database** | Shared library | SQLAlchemy + Aurora Data API, Pydantic models, used by all agents |

**Critical constraint**: LiteLLM + Bedrock cannot combine structured outputs and tool calling on the same agent.

---

## Frontend (Next.js 16, Pages Router)

| Page | Function |
|------|----------|
| `/` | Landing page |
| `/accounts` | Portfolio account management (create, edit, add positions) |
| `/accounts/[id]` | Individual account detail with holdings |
| `/dashboard` | Main analysis dashboard — trigger analysis, view results |
| `/analysis` | Detailed analysis results with charts and reports |
| `/advisor-team` | Describes the AI agent team |

**Stack**: React 19, TypeScript, Tailwind CSS 4, Recharts, Clerk auth, React Markdown.

**Key component**: `AnalysisProgressTracker` — real-time job status updates in the UI.

---

## Operational Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `AWS_START_STOP/deployment_status.py` | Shows what's deployed, costs, health checks |
| `AWS_START_STOP/minimize_costs.py` | Destroys expensive modules (shutdown/minimal/full modes) |
| `AWS_START_STOP/restart_infrastructure.py` | Restores previously destroyed modules |
| `sync_arns.py` | Syncs ARNs to .env and tfvars after infra recreation |
| `verify_arns.py` | Validates ARN consistency across configs |

After recreating infrastructure, always run `sync_arns.py` — Aurora secret ARNs change on every creation.

---

## CI/CD (GitHub Actions)

- **test.yml** — Mock tests on push/PR: backend agent tests (matrix), frontend Jest + Playwright E2E
- **deployment-tests.yml** — Real AWS tests on PR to main/develop (requires GitHub secrets with current ARNs)
- **claude.yml** / **claude-code-review.yml** — Claude-assisted PR reviews

---

## Key Technical Decisions

1. **Aurora Data API** over VPC connectivity — simpler Lambda integration, no connection pools, slight latency tradeoff
2. **S3 Vectors** over OpenSearch — 90% cheaper, serverless, sufficient for the use case
3. **Independent Terraform dirs** — each guide deploys independently, local state only
4. **OpenAI Agents SDK** (`openai-agents`) with LiteLLM — vendor-neutral agent framework running on Bedrock
5. **Nova Pro** over Claude Sonnet — avoids Bedrock rate limits on Anthropic models
6. **Pages Router** over App Router — simpler mental model for the course

---

## What's Needed to Fully Run

1. Restore `5_database`: `cd terraform/5_database && terraform apply`
2. Run migrations: `uv run scripts/run_migrations.py`
3. Sync ARNs: `uv run scripts/sync_arns.py`
4. Repackage/redeploy agents: `cd backend/<agent> && uv run package_docker.py`
5. Optionally restore `4_researcher`: `cd terraform/4_researcher && terraform apply`
6. Verify: `cd scripts/AWS_START_STOP && uv run deployment_status.py`
