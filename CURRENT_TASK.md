# Session Handoff — 2026-04-12 (Session 2)

## Session Goal
Execute cost reduction: destroy redundant CloudFront/S3 infrastructure, confirm App Runner already down, and begin Neon PostgreSQL migration to eliminate Aurora's $55–65/mo cost.

## Completed This Session

### Security Fixes (carried from Session 1 — still uncommitted)
- Fixed CORS logic in `backend/api/main.py` — wildcard only when `CORS_ORIGINS` is literally `"*"`
- Removed `/test-bedrock` debug endpoint from `backend/researcher/server.py`

### Infrastructure Cost Reduction
- **Deleted CloudFront distribution** (`d1hnrs9tdojzww.cloudfront.net`, ID `E18K6AY6UW0RV`) — disabled, waited for propagation, deleted via AWS CLI
- **Deleted S3 frontend bucket** (`alex-frontend-393470797331`) — emptied and deleted via AWS CLI
- **Removed CloudFront + S3 from terraform state** (`terraform/7_frontend`) — 5 resources removed from state
- **Confirmed App Runner (Researcher) already not deployed** — `terraform/4_researcher` state was empty
- **Discovered terraform/7_frontend main.tf is corrupted** — contains Aurora cluster config instead of CloudFront/API Gateway/Lambda. Git history has same corruption (never committed correctly). The API Gateway (`0b75gjui0j`) and Lambda (`alex-api`) remain running in AWS but are now partially orphaned from terraform management. They work fine — just can't be managed via `terraform apply` in that directory.

### Neon Migration Planning
- Installed `neonctl` CLI (v2.22.0) globally via npm
- Completed full migration boundary analysis via explore agent:
  - Mapped entire `DataAPIClient` interface (execute, query, query_one, insert, update, delete, transactions)
  - Identified all 9 model classes that use client.py (none need changes — they call the same interface)
  - Documented all env vars, terraform configs, package_docker.py exclusion lists that reference Aurora
  - Confirmed SQL migrations 001–005 are standard PostgreSQL — run as-is on Neon
  - Confirmed psycopg2-binary fits in Lambda 250MB limit (~3 MB)
- Produced 10-step execution plan (see below)
- **User needs to create Neon account** — sent to https://neon.tech to sign up and get API key

## Files Created / Modified
| File | Action | Notes |
|------|--------|-------|
| `/home/kent_benson/AWS_projects/alex/backend/api/main.py` | modified (Session 1) | CORS fix — still uncommitted |
| `/home/kent_benson/AWS_projects/alex/backend/researcher/server.py` | modified (Session 1) | Removed /test-bedrock — still uncommitted |
| `/home/kent_benson/AWS_projects/alex/EVALUATE_REPORT.md` | created (Session 1) | 34-finding evaluation report |

### AWS Resources Deleted (not files)
| Resource | ID | Method |
|----------|----|--------|
| CloudFront distribution | E18K6AY6UW0RV (`d1hnrs9tdojzww.cloudfront.net`) | AWS CLI delete-distribution |
| S3 bucket | alex-frontend-393470797331 | AWS CLI s3 rm + delete-bucket |
| 5 terraform state entries | CloudFront + S3 + bucket policy/config | terraform state rm |

## Decisions Made
- **Selective destroy, not full module destroy** — terraform/7_frontend contains both the redundant CloudFront/S3 AND the critical API Gateway/Lambda. Destroying the whole module would kill the API backend that Cloudflare Pages depends on. Used targeted AWS CLI deletion + terraform state rm instead.
- **Neon over all other alternatives** — Evaluated RDS t4g.micro ($13/mo), Supabase (pauses after 1 week inactive), SQLite on EFS (single-writer limitation), DynamoDB (requires full rewrite). Neon wins: PostgreSQL-compatible, serverless scale-to-zero, free tier covers single user, standard psycopg2 driver.
- **Single-file migration boundary** — Only `backend/database/src/client.py` needs rewriting. All 9 model classes call `self.db.query()`, `self.db.insert()`, etc. — the interface stays identical. Agent lambda_handlers just do `db = Database()` which reads env vars internally.

## In Progress / Left Off At
The Neon migration is planned but blocked on the user creating a Neon account at https://neon.tech and providing an API key. All analysis and planning is done. The 10-step execution plan is ready:

1. Set up Neon project + get connection string
2. Run migrations 001–005 against Neon
3. Rewrite `backend/database/src/client.py` (boto3 rds-data → psycopg2)
4. Update `backend/database/pyproject.toml` (boto3 → psycopg2-binary)
5. Test locally with `DATABASE_URL` env var
6. Update 6 `package_docker.py` files (exclusion list changes)
7. Update `terraform/6_agents/main.tf` (swap Aurora env vars for DATABASE_URL)
8. Deploy agents via `uv run deploy_all_lambdas.py --package`
9. Destroy Aurora: `cd terraform/5_database && terraform destroy`
10. Clean up: remove sync_arns.py, verify_arns.py, simplify kb_start.py

Security fixes from Session 1 are STILL uncommitted.

## Next Session — Start Here
```
Read CURRENT_TASK.md and resume from there.

PRIORITY 1: Commit the two security fixes (uncommitted since Session 1):
  - backend/api/main.py (CORS fix)
  - backend/researcher/server.py (removed debug endpoint)

PRIORITY 2: Continue Neon migration. I need your Neon API key.
  - Go to https://neon.tech → sign up (free) → Account Settings → API keys → create key
  - Paste the API key and I'll execute the 10-step migration plan
  - neonctl is already installed (v2.22.0)

The migration plan:
  1. Create Neon project with neonctl
  2. Run SQL migrations 001-005
  3. Rewrite backend/database/src/client.py (Aurora Data API → psycopg2)
  4. Update pyproject.toml + 6 package_docker.py files
  5. Test locally, deploy agents, destroy Aurora
  Saves: $55-65/mo permanently

ALSO: terraform/7_frontend/main.tf is corrupted (contains Aurora config
instead of CloudFront/API GW/Lambda). The API Gateway and Lambda still
work but aren't properly managed by terraform. Low priority to fix but
worth noting.

EVALUATE_REPORT.md has 32 remaining findings beyond the 2 security fixes.
```

## Gotchas / Watch Out For
- **TWO SESSIONS of uncommitted changes** — CORS fix and debug endpoint removal in backend/api/main.py and backend/researcher/server.py. Commit these immediately next session.
- **terraform/7_frontend main.tf is corrupted** — Contains Aurora cluster config instead of the CloudFront/API Gateway/Lambda resources that are actually deployed. The state file still tracks the API Gateway + Lambda correctly, but `terraform plan/apply` will fail in this directory. The API Gateway (`https://0b75gjui0j.execute-api.us-east-1.amazonaws.com`) and Lambda (`alex-api`) are running fine — just can't be managed via terraform until main.tf is restored.
- **API Gateway is critical infrastructure** — Do NOT destroy terraform/7_frontend entirely. The API Gateway in that module serves the backend API that Cloudflare Pages frontend (`finance.kentbenson.net`) depends on.
- **Neon free tier limits** — 0.5 GB storage, 190 compute hours/mo, 5-min transaction timeout. All fine for single user, but the Planner's 15-min Lambda timeout with long DB transactions could hit the 5-min limit. In practice, DB transactions in the code are short (individual inserts/updates), not long-running.
- **psycopg2-binary vs psycopg2** — Use `psycopg2-binary` for Lambda (includes compiled libpq). Don't use plain `psycopg2` which requires libpq-dev at build time.
- **After Neon migration**: sync_arns.py and verify_arns.py become obsolete. kb_start.py's ARN sync logic can be removed. The entire "ARN changed after terraform apply" problem disappears — Neon uses a static connection string.
