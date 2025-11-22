# Starting Alex Development Servers

## Quick Start

To start both the API backend and Next.js frontend with automatic VM IP configuration:

```bash
cd /home/kent_benson/AWS_projects/alex
python3 start_dev_server.py
```

Or make it executable and run directly:

```bash
chmod +x start_dev_server.py
./start_dev_server.py
```

## What This Script Does

1. **Auto-detects VM IP**: Automatically finds your VM's external IP address
2. **Configures Environment**: Updates `.env` and `frontend/.env.local` with the correct IP
3. **Starts API Backend**: Launches FastAPI on `http://0.0.0.0:8000` (accessible externally)
4. **Starts Next.js Frontend**: Launches Next.js dev server on `http://localhost:3000`
5. **Monitors Services**: Keeps both running until you press Ctrl+C

## Accessing the Services

After running the script, you'll see output like:

```
============================================================
                    Services Running
============================================================

✓ API Backend:    http://34.173.236.81:8000
✓ API Docs:       http://34.173.236.81:8000/docs
✓ Next.js:        http://34.173.236.81:3000

Access the frontend in your browser at:
  http://34.173.236.81:3000
```

**From your local machine's browser:**
- Frontend: `http://<VM_IP>:3000`
- API Docs: `http://<VM_IP>:8000/docs`

## Stopping the Servers

**Option 1: Using the stop script (recommended):**
```bash
cd /home/kent_benson/AWS_projects/alex
python3 stop_dev_server.py
```

**Option 2: If running in foreground:**
Press `Ctrl+C` in the terminal where the script is running. It will automatically stop both services.

## Manual Start (Alternative)

If you prefer to start services manually:

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

But remember to update the environment files manually:
- `.env`: Set `CORS_ORIGINS=http://localhost:3000,http://<VM_IP>:3000`
- `frontend/.env.local`: Set `NEXT_PUBLIC_API_URL=http://<VM_IP>:8000`

## Firewall Requirements

Ensure these ports are open in your VM's firewall/security group:
- Port 3000 (Next.js frontend)
- Port 8000 (API backend)

## Troubleshooting

### "Failed to fetch" error in browser
- Verify the frontend `.env.local` has the correct VM IP in `NEXT_PUBLIC_API_URL`
- Check that the API backend is accessible: `curl http://<VM_IP>:8000/docs`
- Verify CORS is configured in `.env`: `CORS_ORIGINS` includes your VM IP

### Services won't start
- Check if ports are already in use: `lsof -i :8000` and `lsof -i :3000`
- Kill existing processes: `lsof -ti:8000,3000 | xargs kill -9`
- Try running the script again

### VM IP changed
- Just run `python3 start_dev_server.py` again - it will auto-detect the new IP and reconfigure everything

## Notes

- The VM IP is **non-static** - it may change when you restart the VM
- The script automatically detects the current IP each time it runs
- Make sure to restart the frontend after changing `NEXT_PUBLIC_API_URL` (Next.js embeds this at build time)
