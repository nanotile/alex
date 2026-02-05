# KB Notes

## Feb 5, 2026 — 8-Step Robustness & Informativeness Roadmap COMPLETE

Completed all 8 steps of the Alex enhancement plan. All 5 Lambda agents deployed successfully.

### Steps completed (all committed and pushed)
1. **Charter JSON Validation & Retry** — schema validation + 1 retry on parse failure
2. **Reporter Quality Guard** — raised threshold from 0.3 to 0.6, retry on failure
3. **Data Availability Transparency** — data_sources dict tracks API success/failure, footer in reports
4. **API Rate Limiting** — slowapi middleware (5/min analyze, 30/min POST, 60/min GET)
5. **Benchmark Comparison** — SPY/AGG always included in technical analysis
6. **Dividend & Income Analysis** — estimated annual income, yield-weighted portfolio yield
7. **Richer Retirement Scenarios** — 3 scenarios (conservative/base/optimistic), what-if recommendations, 1000 sims
8. **Historical Performance Tracking** — analysis_history table, snapshot after each analysis, trend comparison

### Lambda packaging breakthrough
All 5 agents now package to ~82MB zipped (under 250MB unzipped limit):
- Added EXCLUDE_PREFIXES for 30+ unused packages (AI provider SDKs, numba, llvmlite, numpy, pandas, etc.)
- Added S3 upload fallback for packages >50MB
- Docker cleanup removes __pycache__, tests, .dist-info, .pyc
- Key finding: `numba` (LLVM JIT) + `llvmlite` were ~50MB — pandas-ta deps, excluded

### Known limitation: pandas-ta excluded from Lambda
Excluding numpy/pandas/numba/llvmlite means `market_data.technical.compute_technical_indicators()` will fail at runtime in Lambda. The Polygon price fetch and other market_data functions still work. Technical indicators were added in the Feb 5 morning session but can't run in Lambda due to the 250MB size limit.

**Fix options for the future:**
- Lambda container images (10GB limit) — best long-term solution
- Pre-compute indicators in a separate service (App Runner or ECS)
- Lambda layer with pandas/numpy (still counts toward 250MB, won't help)

### TODO for next session (Feb 6)
1. **Bring Aurora back up** (destroyed for cost savings):
   ```bash
   cd terraform/5_database && terraform apply
   ```
2. **Sync ARNs** (new secret ARN after terraform apply):
   ```bash
   uv run scripts/sync_arns.py
   ```
3. **Update 6_agents tfvars** with new secret ARN, then apply:
   ```bash
   cd terraform/6_agents && terraform apply
   ```
4. **Run migrations** (includes all 27 statements through migration 006):
   ```bash
   cd backend/database && uv run run_migrations.py
   ```
5. **Test end-to-end** — run a full analysis, verify:
   - Reporter includes data sources footer, quality guard, benchmark comparison, income analysis
   - Charter JSON validation works, charts include benchmark and dividend charts
   - Retirement shows 3 scenarios with what-if recommendations
   - Historical snapshot saved to analysis_history table
6. **Destroy Aurora when done** to save ~$65/mo:
   ```bash
   cd terraform/5_database && terraform destroy
   ```

### All agents deployed (as of Feb 5 evening)
| Agent | Zip Size | Deploy Method |
|-------|----------|---------------|
| alex-planner | 83.0 MB | S3 upload |
| alex-reporter | 81.8 MB | S3 upload |
| alex-tagger | 81.8 MB | S3 upload |
| alex-charter | 82.6 MB | S3 upload |
| alex-retirement | 81.6 MB | S3 upload |

### Commits pushed (9 total)
1. `365bea4` Add pandas-ta technical indicators
2. `f4ee7e1` Add API rate limiting with slowapi
3. `45e186d` Add SPY/AGG benchmark comparison
4. `0080315` Add dividend income analysis
5. `4db31f0` Enhance retirement analysis with 3 scenarios
6. `f0937c5` Add historical performance tracking
7. `1ea0e55` Add charter JSON validation and retry
8. `bab9b7e` Add reporter quality guard with retry
9. `d91aae6` Fix Lambda packaging: exclude numba/llvmlite/numpy/pandas, add S3 deploy

---

## Feb 4, 2026 — Cloudflare Pages Deployment

Deployed Alex frontend to Cloudflare Pages at https://finance.kentbenson.net

### What was done
- Installed wrangler CLI, authenticated with Cloudflare OAuth
- Created Cloudflare Pages project: `finance-kentbenson`
- Built static export with `NEXT_PUBLIC_API_URL` pointing to API Gateway
- Created `frontend/public/_redirects` (dynamic route handling for /accounts/*)
- Created `frontend/public/_headers` (security headers)
- Deployed `out/` to Cloudflare Pages
- Added custom domain `finance.kentbenson.net` (CNAME → finance-kentbenson.pages.dev)
- Updated Lambda `alex-api` CORS_ORIGINS to include `finance.kentbenson.net`

### Infrastructure fixes during deployment
- Aurora cluster was destroyed (cost savings) — recreated with `terraform apply`
- New Aurora Secret ARN: `alex-aurora-credentials-7b2edc73-iXHPpD`
- Updated `.env` with new secret ARN
- Updated `alex-api-lambda-role` IAM policy with new secret ARN
- Ran database migrations (21/21 successful)

### Redeploy command
```bash
cd frontend && NEXT_PUBLIC_API_URL=https://0b75gjui0j.execute-api.us-east-1.amazonaws.com npm run build
wrangler pages deploy out/ --project-name=finance-kentbenson
```

### Cost
- Cloudflare Pages: $0 (free tier)
- Aurora: ~$43/mo (destroy when not working: `cd terraform/5_database && terraform destroy`)

### Previous notes
- Pre-existing ModuleNotFoundError: No module named 'src' on charter — all 5 agent tests have the same issue, unrelated to FRED work.
