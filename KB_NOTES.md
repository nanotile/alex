# KB Notes

## Feb 5, 2026 — pandas-ta Technical Indicators Implementation

Implemented the "future enhancement" from Feb 4 notes — technical indicators computed from Polygon historical price data using pandas-ta.

### What was done (ALL CODE COMPLETE)
- Created `backend/market_data/src/market_data/technical.py` — fetches 300-day OHLCV from Polygon, computes RSI(14), MACD(12,26,9), Bollinger Bands(20,2), SMA(50), SMA(200), EMA(20)
- Created `backend/database/src/technical_models.py` — TechnicalIndicators model with JSONB storage, 1-hour staleness cache
- Created `backend/database/migrations/005_technical_indicators.sql` — new table
- Updated `run_migrations.py` with migration 005 (statements 22-23)
- Added `pandas>=2.0` and `pandas-ta>=0.3.14b` to market_data pyproject.toml
- Wired exports through `__init__.py` files (market_data + database)
- Added `compute_technical_indicators()` to `planner/market.py`, called in `planner/lambda_handler.py` after FRED fetch
- Reporter: added `technical_indicators` to context, `format_technical_indicators()` formatter, "Technical Analysis" section in report prompt
- Charter: `analyze_portfolio()` includes technical data, templates suggest RSI gauge + price vs moving averages charts

### TODO for next session (Feb 6)
1. **Bring Aurora back up** — it's destroyed (cost savings):
   ```bash
   cd terraform/5_database && terraform apply
   ```
2. **Run migration** — creates the `technical_indicators` table (statements 22-23):
   ```bash
   cd backend/database && uv run run_migrations.py
   ```
3. **Repackage Planner Lambda** — Docker image needs pandas/pandas-ta:
   ```bash
   cd backend/planner && uv run package_docker.py
   ```
4. **Repackage Reporter + Charter Lambdas** — they have new code for loading/formatting technical data:
   ```bash
   cd backend/reporter && uv run package_docker.py
   cd backend/charter && uv run package_docker.py
   ```
5. **Test end-to-end** — run a Planner job, verify:
   - Technical indicators populate in `technical_indicators` table
   - Reporter report includes "Technical Analysis" section
   - Charter charts include RSI or moving average visualizations
6. **Destroy Aurora when done** to save ~$43/mo:
   ```bash
   cd terraform/5_database && terraform destroy
   ```

### Files created (3)
- `backend/market_data/src/market_data/technical.py`
- `backend/database/src/technical_models.py`
- `backend/database/migrations/005_technical_indicators.sql`

### Files modified (12)
- `backend/market_data/pyproject.toml` — added pandas, pandas-ta
- `backend/market_data/src/market_data/__init__.py` — export get_technical_indicators
- `backend/database/src/models.py` — import TechnicalIndicators, add db.technical_indicators
- `backend/database/src/__init__.py` — export TechnicalIndicators
- `backend/database/run_migrations.py` — migration 005 statements
- `backend/planner/market.py` — compute_technical_indicators()
- `backend/planner/lambda_handler.py` — calls compute_technical_indicators after FRED
- `backend/reporter/agent.py` — context field, format_technical_indicators(), updated prompt
- `backend/reporter/lambda_handler.py` — loads technical data from DB, passes to agent
- `backend/charter/agent.py` — analyze_portfolio() + create_agent() accept technical_data
- `backend/charter/lambda_handler.py` — loads technical data from DB, passes to agent
- `backend/charter/templates.py` — RSI gauge + price vs MA chart types

### Architecture
```
Planner -> Polygon.io (300-day OHLCV) -> pandas-ta -> Aurora JSONB (1hr cache)
                                                           |
                                               Reporter (text in LLM prompt)
                                               Charter (in portfolio analysis text)
```
Only Planner gets pandas/pandas-ta dependency. Reporter/Charter just read JSONB from DB.

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
