# KB Notes

## Feb 6, 2026 — Test Suite Fixed + Hardening Roadmap

### What was done
- Improved CLAUDE.md with 4 additions (kb_start.py flags, workspace layout, frontend scripts, market_data docs)
- Fixed ALL 112 local mock tests (was 62 pass / 27 fail / 1 syntax error → 112/112 pass)
- No AWS infrastructure needed — all fixes are test-side, matching tests to current source code

### Test fixes applied
| Area | Issue | Files |
|------|-------|-------|
| Planner | Syntax error: `contains` keyword | `planner/tests/test_orchestration.py` |
| Database | Schema tests referenced old Pydantic field names | `database/tests/test_schemas.py` (rewritten) |
| Reporter | `create_agent()` now returns 4 values, takes `user_data` | `reporter/tests/test_agent.py` |
| Reporter | Lambda handler mocks missing DB sub-models | `reporter/tests/test_lambda_handler.py` |
| Shared mocks | Position data missing `symbol` field | `tests_common/mocks.py` |
| Frontend | Missing Clerk mocks: Protect, SignInButton, SignedIn, etc. | `frontend/__mocks__/@clerk/nextjs.tsx` |
| Frontend | ESM modules (react-markdown, remark-gfm, remark-breaks) | 3 new mock files + `jest.config.js` |
| Frontend | Toast test: wrong import type + props mismatch | `frontend/__tests__/components/Toast.test.tsx` |
| Frontend | Layout/Dashboard/Analysis/Index tests: router mocks, fetch mocks | 4 test files rewritten |

### Final test counts
| Component | Passed |
|-----------|--------|
| Frontend (Jest) | 30 |
| Database | 36 |
| Reporter | 22 |
| Planner | 9 |
| Tagger | 15 |
| **Total** | **112** |

Charter and Retirement only have deployment tests (need live Aurora).

### TODO for next session — Hardening & Polish Roadmap

**Recommended approach:** Run as 3 focused sessions (per the ADVICE ON USING COMPACT.md guidance). Each session is one theme, clean context, no compaction needed.

#### Session A: Security & Validation (backend focus)
1. **Timeout wrapping on market data fetches** — Planner calls Polygon, FMP, FRED with no timeout. Wrap each with `asyncio.wait_for(fetch, timeout=30)` and fall back gracefully.
   - File: `backend/planner/lambda_handler.py` lines 51-64
2. **Sanitize Lambda error responses** — All 5 handlers return `str(e)` in catch blocks. Replace with generic messages, log real errors server-side.
   - Files: `*/lambda_handler.py` (all 5 agents)
3. **Add `max_length` to Pydantic string fields** — `display_name`, `account_name`, `account_purpose` have no limits.
   - File: `backend/api/main.py` (UserUpdate, AccountCreate models)
4. **Server-side allocation validation** — Validate `asset_class_targets` and `region_targets` sum to 100% in the API, not just frontend.
   - File: `backend/api/main.py` (UserUpdate model)

#### Session B: Frontend UX (frontend focus)
5. **Differentiate Analysis empty states** — Charts tab shows generic "No chart data available" whether charter failed, is running, or empty. Show different messages per state.
   - File: `frontend/pages/analysis.tsx` lines 346, 447
6. **Add analysis timeout warning** — Show "Taking longer than expected..." after 2 minutes on advisor-team page.
   - File: `frontend/pages/advisor-team.tsx`
7. **Accessibility pass** — Add `role="tablist"`/`role="tab"` to analysis tabs, `aria-label` on charts, `htmlFor` on form labels, `scope="col"` on table headers.
   - Files: `frontend/pages/analysis.tsx`, `frontend/pages/dashboard.tsx`, `frontend/pages/accounts.tsx`
8. **Dashboard "Last Analysis" link** — Change "Never" to a button that navigates to advisor-team.
   - File: `frontend/pages/dashboard.tsx`

#### Session C: Testing & Observability (mixed)
9. **Add API endpoint tests** — `backend/api/main.py` has zero test coverage. Test rate limiting, CORS, input validation, auth.
   - New file: `backend/api/tests/test_main.py`
10. **Add mock tests for Charter and Retirement** — Currently only deployment tests exist.
    - New files: `backend/charter/tests/`, `backend/retirement/tests/`
11. **CloudWatch alarms** — Add alarms for Lambda error rate > 5%, SQS queue age > 10 min.
    - File: new terraform config or `terraform/8_monitoring/`

### Files changed this session (not yet committed)
- `CLAUDE.md` (4 additions)
- `backend/planner/tests/test_orchestration.py`
- `backend/database/tests/test_schemas.py`
- `backend/reporter/tests/test_agent.py`
- `backend/reporter/tests/test_lambda_handler.py`
- `backend/tests_common/mocks.py`
- `frontend/__mocks__/@clerk/nextjs.tsx`
- `frontend/__mocks__/react-markdown.tsx` (new)
- `frontend/__mocks__/remark-gfm.js` (new)
- `frontend/__mocks__/remark-breaks.js` (new)
- `frontend/jest.config.js`
- `frontend/__tests__/components/Toast.test.tsx`
- `frontend/__tests__/components/Layout.test.tsx`
- `frontend/__tests__/pages/index.test.tsx`
- `frontend/__tests__/pages/dashboard.test.tsx`
- `frontend/__tests__/pages/analysis.test.tsx`
- `frontend/test-utils/mockData.ts` (existed, not changed)

---

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
