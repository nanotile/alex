# Starting Alex Development Servers

## Quick Start (Recommended)

Use the master startup script with automatic VM IP detection, ARN sync, and service orchestration:

```bash
cd /home/kent_benson/AWS_projects/alex
python3 kb_start.py
```

This comprehensive script handles everything: IP detection, ARN verification/sync, CORS configuration, and starts both services.

## What kb_start.py Does

1. **System Checks**
   - Detects VM external IP (GCP metadata or ipify.org)
   - Verifies required configuration files exist
   - Checks if terraform database is deployed

2. **ARN Synchronization** (Critical!)
   - Verifies ARNs are in sync across `.env` and `terraform.tfvars`
   - Auto-syncs if mismatches detected
   - Prevents "AccessDenied" errors from stale ARNs

3. **IP Configuration**
   - Updates `.env` with CORS_ORIGINS for current VM IP
   - Updates `frontend/.env.local` with API URL for current VM IP

4. **Service Startup**
   - Stops any existing services on ports 3000 and 8000
   - Starts API backend (uvicorn) on port 8000
   - Starts Next.js frontend on port 3000

5. **Status Reporting**
   - Shows service URLs with current VM IP
   - Monitors services until Ctrl+C

## Alternative Startup Options

### IP Configuration Only
Update configs without starting services:
```bash
python3 kb_start.py --ip-only
```

### ARN Verification Only
Check ARN sync status without starting:
```bash
python3 kb_start.py --verify-only
```

### Skip ARN Check (Not Recommended)
Start services without ARN verification:
```bash
python3 kb_start.py --skip-arn-check
```

## Stopping the Servers

**Recommended method:**
```bash
python3 kb_stop.py
```

**Alternative (if kb_start.py is running in foreground):**
Press `Ctrl+C` - the script handles graceful shutdown

## Current Session Status (2025-11-28)

### Active Services
✅ **Next.js Frontend**: http://34.29.20.131:3000 (PID varies)
✅ **API Backend**: http://34.29.20.131:8000 (PID varies)

### Recent Fixes Applied
- ✅ Next.js config split (dev vs prod) - eliminates static export conflict
- ✅ Turbopack workspace root configured - eliminates lockfile warnings
- ✅ ARN sync scripts added to repository
- ✅ All changes committed and pushed to `cleanup-aws-only` branch

### Configuration Files
- `frontend/next.config.dev.ts` - Development config (SSR enabled)
- `frontend/next.config.prod.ts` - Production config (static export)
- `frontend/package.json` - Auto-copies correct config before dev/build
- `.env` - Backend configuration with CORS
- `frontend/.env.local` - Frontend API URL

## Manual Start (Not Recommended)

If you need to start services manually:

### Terminal 1 - API Backend:
```bash
cd /home/kent_benson/AWS_projects/alex/backend/api
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Next.js Frontend:
```bash
cd /home/kent_benson/AWS_projects/alex/frontend
npm run dev
```

**Important:** Manual start doesn't handle:
- VM IP detection/configuration
- ARN synchronization checks
- Automatic cleanup of old processes
- Status reporting

## Accessing the Services

After starting with `kb_start.py`, access from your browser:

- **Frontend**: http://34.29.20.131:3000 (or your current VM IP)
- **API Docs**: http://34.29.20.131:8000/docs
- **API Health**: http://34.29.20.131:8000/health

## Firewall Requirements

Ensure these ports are open in your GCP firewall:
- **Port 3000** - Next.js frontend
- **Port 8000** - FastAPI backend

## Troubleshooting

### "Next.js frontend stopped unexpectedly"
**Cause**: Configuration issues resolved in latest commit
**Fix**: Pull latest from `cleanup-aws-only` branch and restart
```bash
git pull origin cleanup-aws-only
python3 kb_start.py
```

### "AccessDenied" or "Secret not found" errors
**Cause**: ARN mismatch after database recreation (Aurora secret has random 6-char suffix)
**Fix**: Run ARN sync
```bash
python3 kb_start.py --verify-only  # Check status
python3 kb_start.py                 # Auto-syncs if needed
```

### "Failed to fetch" or CORS errors
**Cause**: Frontend can't reach backend API
**Fix**: Restart with `kb_start.py` to update IP configs
```bash
python3 kb_start.py
```

### Ports already in use
**Cause**: Previous processes not cleaned up
**Fix**: Use kb_start.py (auto-kills old processes) or manual cleanup:
```bash
lsof -ti:8000,3000 | xargs kill -9
python3 kb_start.py
```

### VM IP changed after restart
**Fix**: Just run `kb_start.py` again - it auto-detects and reconfigures
```bash
python3 kb_start.py
```

## Development Workflow

### Daily Startup
```bash
cd /home/kent_benson/AWS_projects/alex
python3 kb_start.py
```

### Daily Shutdown
```bash
python3 kb_stop.py
```

### After Infrastructure Changes
If you've destroyed/recreated database or other infrastructure:
```bash
python3 kb_start.py  # Automatically verifies and syncs ARNs
```

### After Pulling Latest Code
```bash
git pull origin cleanup-aws-only
cd frontend && npm install  # If package.json changed
cd backend/api && uv sync   # If dependencies changed
python3 kb_start.py
```

## Advanced: ARN Management

### Check ARN Synchronization
```bash
uv run scripts/verify_arns.py
```

### Manual ARN Sync
```bash
uv run scripts/sync_arns.py
```

### Dry Run (Preview Changes)
```bash
uv run scripts/sync_arns.py --dry-run
```

### Auto Sync (No Prompts)
```bash
uv run scripts/sync_arns.py --auto
```

## Notes

- **VM IP is non-static**: Changes on VM restart - `kb_start.py` handles this automatically
- **ARN random suffixes**: Aurora secret ARN has 6-char random suffix that changes on recreation
- **Config auto-switching**: `npm run dev` uses dev config, `npm run build` uses prod config
- **Progress tracking disabled**: Set in kb_start.py to avoid performance issues
- **Branch**: Working code is on `cleanup-aws-only` branch

## Recent Updates

**2025-11-28**:
- Fixed Next.js dev/prod config conflict
- Added dual config system (dev vs prod)
- Eliminated Turbopack warnings
- Committed and pushed all utilities to GitHub
- Branch: `cleanup-aws-only`
- Commit: 3cfb252 "Fix Next.js dev/prod config conflict and add dev utilities"

## Next Session Checklist

Before starting work:
1. ✅ Pull latest from GitHub: `git pull origin cleanup-aws-only`
2. ✅ Start services: `python3 kb_start.py`
3. ✅ Verify frontend: http://34.29.20.131:3000 (or current VM IP)
4. ✅ Verify API: http://34.29.20.131:8000/docs
5. ✅ Check ARN sync status (automatic in kb_start.py)

Happy coding! 🚀
