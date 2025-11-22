#!/usr/bin/env python3
"""
Start Alex development servers with automatic VM IP detection.
Configures both frontend and backend to use the VM's external IP address.
"""

import os
import sys
import subprocess
import time
import socket
import urllib.request
from pathlib import Path

# ANSI colors for pretty output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")

def get_vm_external_ip():
    """Get the VM's external IP address."""
    try:
        # Try to get external IP from metadata service (works on GCP, AWS, Azure)
        req = urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip',
            headers={'Metadata-Flavor': 'Google'}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.read().decode('utf-8').strip()
    except:
        pass

    try:
        # Fallback: use external service
        with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
            return response.read().decode('utf-8').strip()
    except:
        pass

    # Last resort: get local network IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return None

def update_env_file(file_path, key, value):
    """Update or add a key-value pair in an env file."""
    file_path = Path(file_path)

    if not file_path.exists():
        print_error(f"{file_path} does not exist!")
        return False

    lines = file_path.read_text().splitlines()
    updated = False

    # Update existing key or add new one
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}")

    file_path.write_text('\n'.join(new_lines) + '\n')
    return True

def kill_existing_processes():
    """Kill existing API and Next.js processes."""
    print_header("Stopping Existing Services")

    # Kill API backend
    try:
        result = subprocess.run("lsof -ti:8000 | xargs kill -9 2>/dev/null",
                              shell=True,
                              capture_output=True)
        if result.returncode == 0:
            print_success("Stopped existing API backend")
        else:
            print_warning("No existing API backend found")
    except:
        print_warning("Could not check for existing API backend")

    # Kill Next.js frontend
    try:
        result = subprocess.run("lsof -ti:3000 | xargs kill -9 2>/dev/null",
                              shell=True,
                              capture_output=True)
        if result.returncode == 0:
            print_success("Stopped existing Next.js frontend")
        else:
            print_warning("No existing Next.js frontend found")
    except:
        print_warning("Could not check for existing Next.js frontend")

    time.sleep(2)

def configure_environment(vm_ip):
    """Configure environment files with VM IP."""
    print_header("Configuring Environment")

    base_dir = Path(__file__).parent

    # Update backend API .env
    backend_env = base_dir / '.env'
    if update_env_file(backend_env, 'CORS_ORIGINS', f'http://localhost:3000,http://{vm_ip}:3000'):
        print_success(f"Updated backend CORS to allow: http://{vm_ip}:3000")

    # Update frontend .env.local
    frontend_env = base_dir / 'frontend' / '.env.local'
    if update_env_file(frontend_env, 'NEXT_PUBLIC_API_URL', f'http://{vm_ip}:8000'):
        print_success(f"Updated frontend API URL to: http://{vm_ip}:8000")

def start_api_backend():
    """Start the FastAPI backend."""
    print_header("Starting API Backend")

    base_dir = Path(__file__).parent
    api_dir = base_dir / 'backend' / 'api'

    if not api_dir.exists():
        print_error(f"API directory not found: {api_dir}")
        return None

    print(f"Starting uvicorn on {BOLD}http://0.0.0.0:8000{RESET}...")

    # Start API in background
    proc = subprocess.Popen(
        ['uv', 'run', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'],
        cwd=api_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for startup
    time.sleep(3)

    # Check if it's running
    try:
        with urllib.request.urlopen('http://localhost:8000/docs', timeout=5) as response:
            if response.status in [200, 304]:
                print_success("API backend is running on http://0.0.0.0:8000")
                return proc
            else:
                print_error("API backend started but not responding correctly")
                return proc
    except:
        print_error("API backend failed to start")
        return None

def start_nextjs_frontend():
    """Start the Next.js frontend."""
    print_header("Starting Next.js Frontend")

    base_dir = Path(__file__).parent
    frontend_dir = base_dir / 'frontend'

    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        return None

    print(f"Starting Next.js dev server on {BOLD}http://localhost:3000{RESET}...")

    # Start Next.js in background
    proc = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for startup
    time.sleep(5)

    # Check if it's running
    try:
        with urllib.request.urlopen('http://localhost:3000', timeout=5) as response:
            if response.status in [200, 304, 307, 308]:
                print_success("Next.js frontend is running on http://localhost:3000")
                return proc
            else:
                print_error("Next.js frontend started but not responding correctly")
                return proc
    except:
        print_error("Next.js frontend failed to start")
        return None

def main():
    """Main entry point."""
    print_header("Alex Development Server Startup")

    # Get VM external IP
    print("Detecting VM external IP address...")
    vm_ip = get_vm_external_ip()

    if not vm_ip:
        print_error("Could not detect VM IP address!")
        sys.exit(1)

    print_success(f"Detected VM IP: {BOLD}{vm_ip}{RESET}")

    # Kill existing processes
    kill_existing_processes()

    # Configure environment
    configure_environment(vm_ip)

    # Start services
    api_proc = start_api_backend()
    if not api_proc:
        print_error("Failed to start API backend. Exiting.")
        sys.exit(1)

    frontend_proc = start_nextjs_frontend()
    if not frontend_proc:
        print_error("Failed to start Next.js frontend. Stopping API backend.")
        api_proc.terminate()
        sys.exit(1)

    # Print final status
    print_header("Services Running")
    print(f"{GREEN}✓{RESET} API Backend:    {BOLD}http://{vm_ip}:8000{RESET}")
    print(f"{GREEN}✓{RESET} API Docs:       {BOLD}http://{vm_ip}:8000/docs{RESET}")
    print(f"{GREEN}✓{RESET} Next.js:        {BOLD}http://{vm_ip}:3000{RESET}")
    print(f"\n{YELLOW}Access the frontend in your browser at:{RESET}")
    print(f"  {BOLD}http://{vm_ip}:3000{RESET}")
    print(f"\n{YELLOW}Note:{RESET} Make sure ports 3000 and 8000 are open in your firewall/security group")
    print(f"\n{RED}Press Ctrl+C to stop all services{RESET}\n")

    # Keep running and forward output
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_header("Shutting Down")
        print("Stopping services...")
        api_proc.terminate()
        frontend_proc.terminate()
        time.sleep(2)
        api_proc.kill()
        frontend_proc.kill()
        print_success("All services stopped")

if __name__ == '__main__':
    main()
