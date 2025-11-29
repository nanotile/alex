# KB Start - Quick Reference Guide

## What Problem Does This Solve?

Running on a **non-static IP VM** creates two synchronization challenges:
1. **VM External IP changes** - Every time you restart the VM
2. **Aurora ARN changes** - Every time you recreate the database

Previously, you had to manually:
- Run `start_dev_server.py` for IP configuration
- Run `verify_arns.py` to check ARN sync
- Run `sync_arns.py` to fix ARN mismatches
- Manually update GitHub Actions secrets
- No clear execution order → confusion and errors

**Now:** One command handles everything automatically!

---

## The Three New Scripts

### 1. `kb_start.py` - Master Startup Script

**Purpose:** Single entry point that orchestrates everything

**What it does:**
1. ✅ Detects VM external IP automatically
2. ✅ Verifies ARN synchronization (auto-fixes if needed)
3. ✅ Configures `.env` and `frontend/.env.local` with correct IP
4. ✅ Starts API backend (port 8000)
5. ✅ Starts Next.js frontend (port 3000)
6. ✅ Reports comprehensive status
7. ✅ Warns about GitHub secrets if database was recreated

**Usage:**
```bash
# Normal startup (recommended)
python3 kb_start.py

# Skip ARN check (not recommended)
python3 kb_start.py --skip-arn-check

# Only update IP, don't start services
python3 kb_start.py --ip-only

# Only verify ARNs, don't start services
python3 kb_start.py --verify-only
```

**Example Output:**
```
======================================================================
               KB Start - Alex Development Environment
======================================================================

ℹ Running system checks...
ℹ Detected VM IP via GCP metadata: 34.29.20.131
✓ VM IP detected: 34.29.20.131
✓ Required configuration files exist

======================================================================
                      ARN Synchronization Check
======================================================================

ℹ Verifying ARN synchronization...
✓ ARNs are in sync - ready to go!

======================================================================
                           IP Configuration
======================================================================

✓ Updated backend CORS: http://localhost:3000,http://34.29.20.131:3000
✓ Updated frontend API URL: http://34.29.20.131:8000

======================================================================
                        Starting API Backend
======================================================================

ℹ Starting uvicorn on http://0.0.0.0:8000...
✓ API backend started successfully

======================================================================
                      Starting Next.js Frontend
======================================================================

ℹ Starting Next.js dev server on http://localhost:3000...
✓ Next.js frontend started successfully

======================================================================
              Alex Development Environment - Ready!
======================================================================

✓ API Backend:    http://34.29.20.131:8000
✓ API Docs:       http://34.29.20.131:8000/docs
✓ Next.js:        http://34.29.20.131:3000

✓ ARNs verified - in sync

──────────────────────────────────────────────────────────────────────
Access the application:
  Frontend: http://34.29.20.131:3000
  API Docs: http://34.29.20.131:8000/docs

Note: Make sure ports 3000 and 8000 are open in your firewall
Press Ctrl+C to stop all services
```

### 2. `kb_stop.py` - Clean Shutdown

**Purpose:** Stops all services and optionally verifies ARN status

**What it does:**
1. ✅ Kills API backend (port 8000)
2. ✅ Kills Next.js frontend (port 3000)
3. ✅ Optionally runs ARN verification to show sync status
4. ✅ Provides restart instructions

**Usage:**
```bash
# Stop all services (default)
python3 kb_stop.py

# Stop services without ARN verification
python3 kb_stop.py --no-verify
```

**Example Output:**
```
======================================================================
                KB Stop - Shutting Down Alex Services
======================================================================

✓ Stopped API Backend (port 8000)
✓ Stopped Next.js Frontend (port 3000)

======================================================================
                    ARN Synchronization Status
======================================================================

ℹ Checking ARN synchronization status...
✅ All ARNs are in sync!

✓  ARNs verified - in sync

======================================================================
                         Shutdown Complete
======================================================================

✓ All services stopped successfully

ℹ To restart: python3 kb_start.py
```

### 3. `update_github_secrets.py` - GitHub Secrets Helper

**Purpose:** Makes updating GitHub Actions secrets trivial

**What it does:**
1. ✅ Reads current ARN values from terraform outputs
2. ✅ Displays ARNs formatted for copy-paste
3. ✅ Provides step-by-step GitHub UI instructions
4. ✅ Offers GitHub CLI automation (if available)
5. ✅ Shows direct link to GitHub secrets page

**Usage:**
```bash
# Interactive guide (default)
python3 update_github_secrets.py

# Just show ARN values
python3 update_github_secrets.py --show-only

# Use GitHub CLI automation
python3 update_github_secrets.py --gh-cli
```

**Example Output:**
```
======================================================================
                 GitHub Actions Secrets Update Guide
======================================================================

ℹ Reading current ARN values from terraform outputs...

📋 Current ARN Values
──────────────────────────────────────────────────────────────────────

AURORA_CLUSTER_ARN:
  arn:aws:rds:us-east-1:393470797331:cluster:alex-aurora-cluster

AURORA_SECRET_ARN:
  arn:aws:secretsmanager:us-east-1:393470797331:secret:alex-aurora-credentials-012072a2-C8hdps

💡 GitHub CLI detected!

Use 'gh' to update secrets automatically? (y/n): y

ℹ Updating secrets for repository: your-user/alex
ℹ Setting AURORA_CLUSTER_ARN...
✓ AURORA_CLUSTER_ARN updated
ℹ Setting AURORA_SECRET_ARN...
✓ AURORA_SECRET_ARN updated

✓ GitHub secrets updated successfully!
ℹ Deployment tests will now use the new ARNs
```

---

## Common Workflows

### Daily Development (VM Restarted)

```bash
# One command does everything!
python3 kb_start.py

# Work on your code...

# Stop when done
python3 kb_stop.py
```

**What happens:**
- ✅ VM IP detected and configured
- ✅ ARNs verified (already in sync from previous work)
- ✅ Services start immediately
- ✅ No manual intervention needed

### Database Just Recreated

```bash
# Start services (ARNs will auto-sync)
python3 kb_start.py

# You'll see warning about GitHub secrets
# Update them with the helper
python3 update_github_secrets.py

# Choose auto-update via gh CLI or manual via GitHub UI
```

**What happens:**
- ⚠️ ARN verification detects mismatch
- 🔄 Auto-sync fixes `.env` and `terraform.tfvars`
- ✅ Services start successfully
- ⚠️ Warning displayed about GitHub secrets
- 📋 Helper script makes GitHub update easy

### Check ARN Status Without Starting Services

```bash
# Just verify ARNs
python3 kb_start.py --verify-only
```

**What happens:**
- ✅ VM IP detected
- ✅ ARN verification runs
- ✅ Status reported
- ℹ️ Services not started

### Update IP Configuration Only

```bash
# Just update IP settings
python3 kb_start.py --ip-only
```

**What happens:**
- ✅ VM IP detected
- ✅ `.env` and `frontend/.env.local` updated
- ℹ️ Services not started

---

## Troubleshooting

### "ARN sync failed! Manual intervention required"

**Problem:** Auto-sync couldn't fix ARN mismatch

**Solution:**
```bash
# Run sync manually
uv run scripts/sync_arns.py

# Verify it worked
uv run scripts/verify_arns.py

# Try starting again
python3 kb_start.py
```

### "Could not detect VM IP address"

**Problem:** All IP detection methods failed

**Solution:**
- Check network connectivity
- Verify you're on a GCP VM or have internet access
- Manually set IP in `.env` and `frontend/.env.local`

### "Services fail with AccessDenied errors"

**Problem:** ARNs are out of sync with deployed infrastructure

**Solution:**
```bash
# Verify ARN status
python3 kb_start.py --verify-only

# If out of sync, sync will run automatically
# Or force sync manually
uv run scripts/sync_arns.py
```

### "GitHub Actions deployment tests failing"

**Problem:** GitHub secrets have old ARN values

**Solution:**
```bash
# Use the helper to update secrets
python3 update_github_secrets.py

# Follow prompts to update via gh CLI or manually
```

---

## File Locations

### Configuration Files Updated by kb_start.py

1. **`.env`** (root directory)
   - `CORS_ORIGINS` - Updated with VM IP
   - `AURORA_CLUSTER_ARN` - Synced from terraform
   - `AURORA_SECRET_ARN` - Synced from terraform

2. **`frontend/.env.local`**
   - `NEXT_PUBLIC_API_URL` - Updated with VM IP

3. **`terraform/6_agents/terraform.tfvars`**
   - `aurora_cluster_arn` - Synced from terraform
   - `aurora_secret_arn` - Synced from terraform

### ARN Source of Truth

**`terraform/5_database/terraform.tfstate`**
- Contains actual deployed ARN values
- Used by `sync_arns.py` to update config files

---

## Benefits

### Before kb_start.py

❌ Manual multi-step process
❌ Confusing execution order
❌ Easy to forget steps
❌ Cryptic error messages
❌ No guidance on GitHub secrets
❌ Manual ARN copy-paste (error-prone)

### After kb_start.py

✅ Single command startup
✅ Automatic IP detection
✅ Automatic ARN synchronization
✅ Clear status reporting
✅ Explicit warnings about GitHub secrets
✅ Helper script for easy updates
✅ Self-documenting workflow

---

## Integration with Existing Scripts

### Old Scripts (Still Work)

- `start_dev_server.py` - Still works, but doesn't handle ARN sync
- `stop_dev_server.py` - Still works
- `scripts/verify_arns.py` - Used internally by kb_start.py
- `scripts/sync_arns.py` - Used internally by kb_start.py

### Recommended Migration

**Replace:**
```bash
python3 start_dev_server.py
```

**With:**
```bash
python3 kb_start.py
```

**Replace:**
```bash
python3 stop_dev_server.py
```

**With:**
```bash
python3 kb_stop.py
```

---

## Next Steps

1. ✅ Test kb_start.py with your current setup
2. ✅ Recreate database to test ARN auto-sync
3. ✅ Update GitHub secrets using helper script
4. ✅ Update documentation to reference kb_start.py
5. ✅ Consider deprecating old start_dev_server.py

---

## Questions?

- **What if I want to skip ARN check?** Use `--skip-arn-check` (not recommended)
- **Can I just update IP?** Yes, use `--ip-only`
- **Can I verify ARNs without starting?** Yes, use `--verify-only`
- **Does this work on AWS VMs?** Yes, IP detection works on GCP, AWS, and generic VMs
- **What about Windows/Mac?** Works on all platforms with Python 3.7+

---

*Created: November 2025*
*Author: KB (Kent Benson)*
*Project: Alex - AI in Production*
