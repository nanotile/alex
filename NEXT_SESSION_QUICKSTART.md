# Next Session Quick Start

## 🚀 One-Command Startup

```bash
cd /home/kent_benson/AWS_projects/alex
python3 kb_start.py
```

That's it! The script handles everything automatically.

## 📋 What It Does

✅ Detects your VM's current IP (handles IP changes)
✅ Verifies ARN synchronization (prevents auth errors)
✅ Updates CORS and API URL configs
✅ Stops old processes on ports 3000 & 8000
✅ Starts API backend (port 8000)
✅ Starts Next.js frontend (port 3000)
✅ Shows you the service URLs

## 🌐 Access Your Services

**Frontend**: http://34.29.20.131:3000 *(or current VM IP)*
**API Docs**: http://34.29.20.131:8000/docs

## 🛑 Stopping Services

```bash
python3 kb_stop.py
```

Or press `Ctrl+C` if kb_start.py is running in foreground.

## ⚡ Quick Commands

```bash
# Status check
curl http://localhost:3000        # Frontend health
curl http://localhost:8000/docs   # API docs

# ARN management
uv run scripts/verify_arns.py     # Check ARN sync
uv run scripts/sync_arns.py       # Manual sync

# Git updates
git pull origin cleanup-aws-only  # Get latest code
git status                        # Check changes
```

## ⚠️ Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Services won't start | `python3 kb_start.py` (auto-kills old processes) |
| VM IP changed | `python3 kb_start.py` (auto-detects and reconfigures) |
| ARN errors | `python3 kb_start.py` (auto-syncs ARNs) |
| CORS errors | `python3 kb_start.py` (updates CORS config) |
| Port already in use | `lsof -ti:8000,3000 \| xargs kill -9` then `python3 kb_start.py` |

## 📝 Session Notes (2025-11-28)

### What's Fixed
✅ Next.js config conflict resolved (dual config system)
✅ Turbopack warnings eliminated
✅ Frontend stability issues fixed
✅ All utilities committed to GitHub

### Current Branch
**cleanup-aws-only** *(not main!)*

### Latest Commit
```
3cfb252 - Fix Next.js dev/prod config conflict and add dev utilities
```

## 🔧 Important Files

| File | Purpose |
|------|---------|
| `frontend/next.config.dev.ts` | Dev config (SSR enabled) |
| `frontend/next.config.prod.ts` | Prod config (static export) |
| `kb_start.py` | Master startup script |
| `kb_stop.py` | Shutdown script |
| `scripts/sync_arns.py` | ARN sync utility |
| `.env` | Backend config (CORS) |
| `frontend/.env.local` | Frontend config (API URL) |

## 💡 Pro Tips

1. **Always pull first**: `git pull origin cleanup-aws-only`
2. **Use kb_start.py**: Don't start services manually
3. **Check ARN sync**: Automatic in kb_start.py
4. **VM IP changes**: Just re-run kb_start.py
5. **Keep on cleanup-aws-only branch**: Working code is here

## 📚 More Info

- **Full guide**: `START_SERVER_README.md`
- **Session details**: `SESSION_2025-11-28_SUMMARY.md`
- **Project docs**: `CLAUDE.md`

---

**Ready to code!** 🎉

Just run `python3 kb_start.py` and you're good to go.
