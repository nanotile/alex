# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Alex (Agentic Learning Equities eXplainer) is a multi-agent SaaS financial planning platform deployed on AWS. It's the capstone project for Ed Donner's "AI in Production" Udemy course (Weeks 3-4). The user is a student building Alex incrementally through 8 guides in `guides/` (read these for full context before helping).

## Commands

### Backend (Python/uv) — each agent dir is its own uv project
```bash
cd backend/<agent> && uv run pytest test_simple.py          # Local tests with mocks (MOCK_LAMBDAS=true)
cd backend/<agent> && uv run pytest test_full.py             # Deployment tests (real AWS)
cd backend/<agent> && uv run pytest test_simple.py::test_fn -v  # Single test
cd backend/<agent> && uv run package_docker.py               # Package for Lambda (Docker must be running!)
cd backend/<agent> && uv add <package>                       # Add dependency
```

### Frontend (NextJS — Pages Router, not App Router)
```bash
cd frontend && npm run dev          # Dev server (localhost:3000)
cd frontend && npm run build        # Production build
cd frontend && npm test             # Jest unit tests
cd frontend && npm run test:e2e     # Playwright E2E tests
cd frontend && npm run lint         # Lint
```

### Terraform — each directory is independent with local state
```bash
cd terraform/<N_name> && terraform init     # First time only
cd terraform/<N_name> && terraform plan     # Preview
cd terraform/<N_name> && terraform apply    # Deploy
cd terraform/<N_name> && terraform output   # Get ARNs/URLs
cd terraform/<N_name> && terraform destroy  # Teardown
```
Each dir needs `terraform.tfvars` copied from `terraform.tfvars.example` and configured before apply.

### ARN Sync (critical after recreating infrastructure)
```bash
uv run scripts/sync_arns.py            # Sync ARNs to .env and tfvars
uv run scripts/sync_arns.py --dry-run  # Preview only
uv run scripts/verify_arns.py          # Check for mismatches
```

### Cost Management
```bash
cd scripts/AWS_START_STOP && uv run deployment_status.py     # What's deployed
cd scripts/AWS_START_STOP && uv run minimize_costs.py        # Destroy expensive resources
cd scripts/AWS_START_STOP && uv run restart_infrastructure.py # Restore resources
```

### Git — use project utilities, not raw git commands
```bash
uv run KB_github_UTILITIES/git_utilities/github_new_branch.py       # Create + push branch
uv run KB_github_UTILITIES/git_utilities/what_has_changed_in_branch.py  # Compare branches
uv run KB_github_UTILITIES/git_utilities/burn_it_down_start_new.py  # Delete branch, start fresh
```

## Architecture

### Agent Orchestration Flow
```
User → NextJS/Clerk → FastAPI (Lambda) → SQS → Planner (Orchestrator)
                                                  ├→ Polygon.io ─→ real-time prices
                                                  ├→ FMP API    ─→ company fundamentals → Aurora DB
                                                  ├→ FRED API   ─→ economic indicators → Aurora DB
                                                  ├→ Tagger     ─→ Aurora DB
                                                  ├→ Reporter   ─→ Aurora DB + S3 Vectors + economic context
                                                  ├→ Charter    ─→ Aurora DB
                                                  └→ Retirement ─→ Aurora DB
Researcher (App Runner) ← Reporter (for market research context)
S3 Vectors ← SageMaker Embeddings (all-MiniLM-L6-v2)
All agents use AWS Bedrock Nova Pro via LiteLLM
```

### Agent Code Pattern (every agent follows this)
Each agent directory contains: `lambda_handler.py`, `agent.py`, `templates.py`, `test_simple.py`, `test_full.py`, `package_docker.py`

```python
# lambda_handler.py — standard pattern
from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel

os.environ["AWS_REGION_NAME"] = bedrock_region  # MUST be AWS_REGION_NAME for LiteLLM

model = LitellmModel(model=f"bedrock/{model_id}")

with trace("Agent Name"):
    agent = Agent(
        name="Agent Name",
        instructions=INSTRUCTIONS,  # from templates.py
        model=model,
        tools=tools  # OR use output_type for structured outputs — NEVER both
    )
    result = await Runner.run(agent, input=task, max_turns=20)
    response = result.final_output
```

**Critical constraint**: LiteLLM + Bedrock cannot use structured outputs AND tool calling on the same agent. Choose one per agent.

**Context passing for tools** (when tool needs user context):
```python
agent = Agent[ReporterContext](name="Reporter", ...)
result = await Runner.run(agent, input=task, context=context)

@function_tool
async def my_tool(wrapper: RunContextWrapper[ReporterContext], arg: str) -> str: ...
```

### Key Infrastructure Decisions
- **Aurora Data API** (not VPC): simpler Lambda integration, no connection pools, slight latency tradeoff
- **S3 Vectors** (not OpenSearch): 90% cheaper, serverless
- **Independent Terraform dirs**: each guide deploys independently, local state, no remote backend
- **OpenAI Agents SDK** via `openai-agents` package (import as `from agents import ...`)
- **Nova Pro model** (not Claude Sonnet): avoids Bedrock rate limits

### Infrastructure by Guide
| Guide | Resources | Cost |
|-------|-----------|------|
| 2 | SageMaker Serverless endpoint | ~$0.20/hr idle |
| 3 | S3 Vectors, Lambda, API Gateway | ~$5/mo |
| 4 | App Runner (Researcher), ECR | ~$5/mo |
| 5 | Aurora Serverless v2 PostgreSQL | **~$40/mo** |
| 6 | 5 Lambda agents, SQS, S3 packages | ~$10/mo |
| 7 | CloudFront, S3, API Gateway Lambda | ~$5/mo |
| 8 | CloudWatch dashboards | ~$5/mo |

Aurora (Guide 5) is the biggest cost. Destroy when not working: `cd terraform/5_database && terraform destroy`

## Critical Rules

### Package Management
- **Always `uv`**: `uv add`, `uv run`, `uv run pytest`. Never `pip install`, never bare `python`.
- Each backend agent dir has its own `pyproject.toml`. Nested uv projects are fine.
- Correct package: `uv add openai-agents` (not `agents`)

### Platform
- Student may be on Windows, Mac, or Linux. Prefer Python scripts over shell scripts.
- Docker must be running for `package_docker.py`. Docker build targets `linux/amd64`.

### Approach
- **Diagnose before fixing**: don't write code before understanding the root cause. One change at a time.
- **Ask which guide** the student is on — this determines what infrastructure exists.
- **Read the guides** in `guides/` before helping with guide-specific work.

## Common Troubleshooting

**`package_docker.py` fails**: Docker Desktop not running. Check with `docker ps`. Mounts Denied → add path to Docker Desktop File Sharing settings.

**Bedrock "Access denied" / "Model not found"**: Wrong region or model access not granted. LiteLLM requires `AWS_REGION_NAME` (not `AWS_REGION`). Check Bedrock console model access. Nova Pro needs inference profiles for cross-region.

**Terraform fails**: Missing `terraform.tfvars` (copy from `.example`). For later guides, get ARNs from earlier `terraform output`.

**"AccessDenied" after recreating infrastructure**: ARNs changed (Aurora secret ARN has random suffix). Run `uv run scripts/sync_arns.py` then redeploy agents.

**Lambda errors**: Check CloudWatch logs: `aws logs tail /aws/lambda/alex-<agent> --follow`. Verify env vars and IAM permissions.

## CI/CD

- **Mock Tests** (`.github/workflows/test.yml`): Runs on push/PR. Backend mocks + frontend Jest/Playwright. No AWS needed.
- **Deployment Tests** (`.github/workflows/deployment-tests.yml`): Runs on PR to main/develop. Real AWS infrastructure. Requires GitHub secrets with current ARNs.
- After infrastructure recreation, GitHub secrets must be updated with new ARNs.

## Domain Context (from Cursor rules)

- **Tagger**: Classifies instruments by asset class, region, sector, market cap. Allocations must sum to 100%.
- **Planner**: Orchestrates staged workflow — data gathering (Polygon prices, FMP fundamentals, FRED economic indicators), parallel agent dispatch, results aggregation.
- **Reporter**: Portfolio analysis with FMP fundamentals, FRED economic context (rates, inflation, GDP, VIX), and market research from Researcher agent/S3 Vectors.
- **Charter**: Generates visualizations and charts from analysis data.
- **Retirement**: Monte Carlo simulations for retirement projections, dynamic withdrawal modeling, safe withdrawal rate calculation, portfolio survival probability.
