# Investing_2026 Application State — February 4, 2026

## What Investing_2026 Is

Investing_2026 (Agentic Learning Equities eXplainer) is a multi-agent SaaS financial planning platform deployed on AWS. It analyzes investment portfolios, generates reports with charts, runs retirement projections via Monte Carlo simulation, and autonomously researches market trends. Built as a capstone for Ed Donner's "AI in Production" Udemy course (Weeks 3-4), following 8 incremental deployment guides in `guides/`.

---

## How It Works (End-to-End Flow)

```
User (browser)
  → Next.js frontend (Clerk auth, CloudFront CDN)
    → FastAPI API (Lambda via API Gateway)
      → SQS job queue
        → Planner agent (Lambda) — orchestrator
            ├→ Polygon.io   — real-time stock prices
            ├→ FMP API      — company fundamentals (PE, dividends, sector, market cap)
            ├→ FRED API     — macro-economic indicators (rates, inflation, unemployment, GDP, VIX)
            ├→ Tagger agent    — classifies instruments by asset class/region/sector
            ├→ Reporter agent  — portfolio analysis + fundamentals + economic context + S3 Vectors
            ├→ Charter agent   — generates interactive chart data
            └→ Retirement agent — Monte Carlo retirement projections (1000+ scenarios)

Researcher agent (App Runner, every 2 hours)
  → scrapes financial sites with Playwright
  → ingests via Lambda → Bedrock Titan embedding + SageMaker FinBERT sentiment
  → stores in S3 Vectors knowledge base (with sentiment_label + sentiment_score metadata)
  → Reporter queries this context during analysis (sentiment shown inline)

All AI agents use AWS Bedrock Nova Pro via LiteLLM + OpenAI Agents SDK
All agents share Aurora PostgreSQL (Data API) via the alex-database package
Market data APIs shared via the alex-market-data package (Polygon + FMP + FRED + Sentiment)
```

---

## Infrastructure Map

| Module | What It Deploys | Monthly Cost | Current Status |
|--------|----------------|-------------|----------------|
| **2_sagemaker** | SageMaker serverless FinBERT sentiment endpoint (ProsusAI/finbert, text-classification, 3GB) | ~$10 | **Deployed** (Feb 4, 2026) |
| **3_ingestion** | S3 Vectors bucket + Lambda ingestion (embedding + sentiment) + API Gateway (key auth, rate limited) | ~$1-5 | **Deployed** (Feb 4, 2026) |
| **4_researcher** | ECR repo + App Runner service (1 vCPU, 2GB) for autonomous research | ~$51 | **Destroyed** (cost savings) |
| **5_database** | Aurora Serverless v2 PostgreSQL 15.12 + Secrets Manager (Data API) | ~$65 | **Destroyed** (cost savings) |
| **6_agents** | 5 Lambda functions + SQS queue + DLQ + IAM roles + CloudWatch logs | ~$1 | Likely deployed |
| **7_frontend** | CloudFront + S3 static site + API Gateway Lambda proxy | ~$2 | Likely deployed |
| **8_enterprise** | 2 CloudWatch dashboards | ~$5 | Likely deployed |

**Last recorded state**: Feb 4, 2026 — deployed FinBERT sentiment endpoint (2_sagemaker) and updated ingest Lambda (3_ingestion) with sentiment scoring. Modules `4_researcher` and `5_database` remain destroyed for cost savings.

**Estimated running cost**: ~$19/month (without Aurora & Researcher). Full deployment: ~$135/month.

**Note**: Terraform state for `3_ingestion` is out of sync — Lambda was updated directly via AWS CLI on Feb 4, 2026. Run `terraform import` or `terraform destroy && terraform apply` to re-sync state before making further terraform changes to that module.

Each Terraform module is independent with local state. No remote backend.

---

## Database Schema (Aurora PostgreSQL)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **users** | User profiles | clerk_user_id (PK), display_name, years_until_retirement, target_retirement_income, asset_class_targets (JSONB), region_targets (JSONB) |
| **instruments** | Financial reference data | symbol (PK), name, instrument_type, current_price, allocation by region/sector/asset_class (JSONB) |
| **instrument_fundamentals** | FMP data cache (24h TTL) | symbol (PK, FK→instruments), company_name, sector, industry, market_cap, pe_ratio, pb_ratio, dividend_yield, roe, debt_to_equity, eps, beta, 52-week range, avg_volume, fetched_at |
| **economic_indicators** | FRED data cache (6h TTL) | series_id (PK), series_name, latest_value, latest_date, previous_value, previous_date, units, frequency, fetched_at |
| **accounts** | Portfolio accounts | id (UUID), clerk_user_id (FK), account_name, account_purpose, cash_balance |
| **positions** | Holdings per account | id (UUID), account_id (FK), symbol (FK), quantity (DECIMAL 20,8), as_of_date. Unique on (account_id, symbol) |
| **jobs** | Analysis job tracking | id (UUID), clerk_user_id (FK), status (pending/running/completed/failed), report_payload, charts_payload, retirement_payload, summary_payload (all JSONB) |

---

## Backend Agents (each is a uv project under `backend/`)

| Agent/Package | Runtime | Role |
|-------|---------|------|
| **api** | Lambda (FastAPI + Mangum) | REST API for frontend, Clerk auth, user/portfolio/job CRUD |
| **planner** | Lambda | Orchestrator — receives SQS jobs, fetches prices (Polygon) + fundamentals (FMP) + economic indicators (FRED), dispatches specialists |
| **tagger** | Lambda | Classifies instruments by asset class, region, sector (structured output, no tools) |
| **reporter** | Lambda | Portfolio analysis with FMP fundamentals + FRED economic context + S3 Vectors market context (tool calling, no structured output) |
| **charter** | Lambda | Generates 4-6 chart specifications from analysis data |
| **retirement** | Lambda | Monte Carlo simulations — withdrawal modeling, survival probability |
| **researcher** | App Runner (FastAPI) | Autonomous web scraper, embeds findings into S3 Vectors |
| **ingest** | Lambda | Document vectorization (Bedrock Titan) + sentiment scoring (SageMaker FinBERT) into S3 Vectors |
| **database** | Shared library | Aurora Data API client, Pydantic models, used by all agents |
| **market_data** | Shared library | FMP API client, FRED API client, Polygon price fetcher, SentimentClient (FinBERT via SageMaker), unified price interface, used by planner/reporter/tagger/ingest |

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
7. **Shared market_data package** — same pattern as database package; wraps Polygon + FMP + FRED, extensible for sentiment/alternative data later
8. **Separate instrument_fundamentals table** — avoids modifying existing instruments table; 24-hour staleness cache; graceful degradation if FMP unavailable
9. **Separate economic_indicators table** — keyed by FRED series_id (not symbol); economy-wide data shared across all portfolios; 6-hour staleness cache; graceful degradation if FRED unavailable
10. **FinBERT sentiment at ingest time** — repurposed idle SageMaker embedding endpoint for ProsusAI/finbert (text-classification); sentiment scored once during ingest, stored as S3 Vectors metadata (sentiment_label + sentiment_score); Reporter surfaces sentiment inline in market insights; zero additional infrastructure cost

---

## Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `POLYGON_API_KEY` | market_data, planner | Polygon.io stock prices |
| `POLYGON_PLAN` | market_data, planner | "paid" or free tier |
| `FMP_API_KEY` | market_data, planner | Financial Modeling Prep fundamentals |
| `FRED_API_KEY` | market_data, planner | FRED macro-economic indicators (free at fred.stlouisfed.org) |
| `AURORA_CLUSTER_ARN` | database | Aurora Data API |
| `AURORA_SECRET_ARN` | database | Aurora Data API auth |
| `AURORA_DATABASE` | database | Database name (default: "alex") |
| `BEDROCK_MODEL_ID` | all agents | Bedrock model for LLM calls |
| `BEDROCK_REGION` | all agents | AWS region for Bedrock |
| `SAGEMAKER_SENTIMENT_ENDPOINT` | ingest, market_data | SageMaker FinBERT endpoint name (default: alex-sentiment-endpoint) |

---

## What's Needed to Fully Run

1. Restore `5_database`: `cd terraform/5_database && terraform apply`
2. Run migrations: `cd backend/database && uv run python run_migrations.py` (includes instrument_fundamentals + economic_indicators tables)
3. Sync ARNs: `uv run scripts/sync_arns.py`
4. Set `FMP_API_KEY` and `FRED_API_KEY` in `.env` and Lambda environment variables
5. Repackage/redeploy agents: `cd backend/<agent> && uv run package_docker.py`
6. Optionally restore `4_researcher`: `cd terraform/4_researcher && terraform apply`
7. Verify: `cd scripts/AWS_START_STOP && uv run deployment_status.py`
