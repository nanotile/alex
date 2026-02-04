# KB Notes

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
