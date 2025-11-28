#!/usr/bin/env python3
"""
KB Start - Master startup script for Alex development environment

Handles dual synchronization challenges on non-static IP VM:
- VM IP detection and configuration
- ARN synchronization verification and auto-sync
- Service startup (API + Frontend)
- Comprehensive status reporting

Usage:
    python3 kb_start.py                    # Start everything (recommended)
    python3 kb_start.py --skip-arn-check  # Skip ARN verification (not recommended)
    python3 kb_start.py --ip-only         # Only update IP, don't start services
    python3 kb_start.py --verify-only     # Only verify ARNs, don't start services

Author: KB (Kent Benson)
Project: Alex - AI in Production
"""

import os
import sys
import subprocess
import time
import socket
import urllib.request
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ANSI colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Import ARN management classes from existing scripts
sys.path.insert(0, str(Path(__file__).parent))
from scripts.sync_arns import ARNSyncManager, Colors as ARNColors
from scripts.verify_arns import ARNVerifier


def print_header(text: str):
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ{Colors.RESET} {text}")


# ============================================================================
# PHASE 1: SYSTEM CHECKS
# ============================================================================

def get_vm_external_ip() -> Optional[str]:
    """
    Get the VM's external IP address using multiple methods.

    Tries in order:
    1. GCP metadata service
    2. External IP service (ipify.org)
    3. Local network IP (fallback)

    Returns:
        str: External IP address or None if detection fails
    """
    # Try GCP metadata service first (works on GCP VMs)
    try:
        req = urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip',
            headers={'Metadata-Flavor': 'Google'}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            ip = response.read().decode('utf-8').strip()
            print_info(f"Detected VM IP via GCP metadata: {ip}")
            return ip
    except Exception:
        pass

    # Fallback: use external service
    try:
        with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
            ip = response.read().decode('utf-8').strip()
            print_info(f"Detected VM IP via ipify.org: {ip}")
            return ip
    except Exception:
        pass

    # Last resort: get local network IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print_info(f"Using local network IP: {ip}")
        return ip
    except Exception:
        return None


def check_terraform_deployed() -> bool:
    """
    Check if critical terraform modules are deployed.

    Returns:
        bool: True if database is deployed (minimum requirement)
    """
    project_root = Path(__file__).parent
    database_state = project_root / "terraform/5_database/terraform.tfstate"

    if not database_state.exists():
        print_warning("Database terraform state not found")
        print_info("Database must be deployed for ARN synchronization")
        print_info("Deploy: cd terraform/5_database && terraform apply")
        return False

    return True


def check_required_files() -> bool:
    """
    Verify that required configuration files exist.

    Returns:
        bool: True if all required files exist
    """
    project_root = Path(__file__).parent
    required_files = [
        project_root / ".env",
        project_root / "frontend/.env.local",
    ]

    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))

    if missing_files:
        print_error("Missing required configuration files:")
        for file_path in missing_files:
            print(f"  • {file_path}")
        print_info("Create these files from their .example templates")
        return False

    return True


# ============================================================================
# PHASE 2: ARN SYNCHRONIZATION
# ============================================================================

def verify_and_sync_arns(skip_check: bool = False) -> Dict:
    """
    Verify ARNs are in sync. If not, auto-sync and re-verify.

    Args:
        skip_check: Skip ARN verification (not recommended)

    Returns:
        dict: {
            "synced": bool,
            "auto_synced": bool,
            "actions_needed": List[str]
        }
    """
    if skip_check:
        print_warning("Skipping ARN verification (--skip-arn-check flag)")
        return {"synced": True, "auto_synced": False, "actions_needed": []}

    print_header("ARN Synchronization Check")

    project_root = Path(__file__).parent

    # Check if database is deployed
    if not check_terraform_deployed():
        print_warning("Database not deployed - skipping ARN sync")
        return {"synced": True, "auto_synced": False, "actions_needed": []}

    # Run verify_arns.py
    print_info("Verifying ARN synchronization...")
    verifier = ARNVerifier(project_root)
    is_synced = verifier.verify()

    if is_synced:
        print_success("ARNs are in sync - ready to go!")
        return {"synced": True, "auto_synced": False, "actions_needed": []}

    # ARNs out of sync - auto-fix
    print_warning("ARNs are out of sync. Auto-syncing now...")
    print()

    sync_manager = ARNSyncManager(project_root)
    sync_manager.sync(dry_run=False, auto=True)

    # Re-verify after sync
    print()
    print_info("Re-verifying ARN synchronization...")
    verifier_after = ARNVerifier(project_root)
    is_synced_after = verifier_after.verify()

    if not is_synced_after:
        print_error("ARN sync failed! Manual intervention required.")
        print_info("Run manually: uv run scripts/sync_arns.py")
        sys.exit(1)

    print_success("ARN synchronization complete!")

    # Check if GitHub secrets likely need updating
    # (If database was recently deployed, secrets are probably stale)
    actions_needed = []
    database_state = project_root / "terraform/5_database/terraform.tfstate"

    if database_state.exists():
        import json
        try:
            with open(database_state, 'r') as f:
                state_data = json.load(f)
                # Check if state is recent (modified in last hour)
                import os
                state_mtime = os.path.getmtime(database_state)
                current_time = time.time()
                if current_time - state_mtime < 3600:  # 1 hour
                    actions_needed.append("Update GitHub Actions secrets (AURORA_CLUSTER_ARN, AURORA_SECRET_ARN)")
        except Exception:
            pass

    return {
        "synced": True,
        "auto_synced": True,
        "actions_needed": actions_needed
    }


# ============================================================================
# PHASE 3: IP CONFIGURATION
# ============================================================================

def update_env_file(file_path: Path, key: str, value: str) -> bool:
    """
    Update or add a key-value pair in an env file.

    Args:
        file_path: Path to env file
        key: Environment variable name
        value: Environment variable value

    Returns:
        bool: True if update succeeded
    """
    if not file_path.exists():
        print_error(f"{file_path} does not exist!")
        return False

    try:
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
    except Exception as e:
        print_error(f"Failed to update {file_path}: {e}")
        return False


def configure_ip_settings(vm_ip: str):
    """
    Configure environment files with VM IP for CORS and API URL.

    Args:
        vm_ip: External IP address of the VM
    """
    print_header("IP Configuration")

    base_dir = Path(__file__).parent

    # Update backend API .env for CORS
    backend_env = base_dir / '.env'
    cors_value = f'http://localhost:3000,http://{vm_ip}:3000'
    if update_env_file(backend_env, 'CORS_ORIGINS', cors_value):
        print_success(f"Updated backend CORS: {cors_value}")

    # Update frontend .env.local for API URL
    frontend_env = base_dir / 'frontend' / '.env.local'
    api_url = f'http://{vm_ip}:8000'
    if update_env_file(frontend_env, 'NEXT_PUBLIC_API_URL', api_url):
        print_success(f"Updated frontend API URL: {api_url}")


# ============================================================================
# PHASE 4: SERVICE STARTUP
# ============================================================================

def kill_existing_processes():
    """Kill existing API backend and Next.js frontend processes."""
    print_header("Stopping Existing Services")

    # Kill API backend (port 8000)
    try:
        result = subprocess.run(
            "lsof -ti:8000 | xargs kill -9 2>/dev/null",
            shell=True,
            capture_output=True
        )
        if result.returncode == 0:
            print_success("Stopped existing API backend")
        else:
            print_info("No existing API backend found")
    except Exception:
        print_warning("Could not check for existing API backend")

    # Kill Next.js frontend (port 3000)
    try:
        result = subprocess.run(
            "lsof -ti:3000 | xargs kill -9 2>/dev/null",
            shell=True,
            capture_output=True
        )
        if result.returncode == 0:
            print_success("Stopped existing Next.js frontend")
        else:
            print_info("No existing Next.js frontend found")
    except Exception:
        print_warning("Could not check for existing Next.js frontend")

    time.sleep(2)


def start_api_backend() -> Optional[subprocess.Popen]:
    """
    Start the FastAPI backend on port 8000.

    Returns:
        subprocess.Popen: Backend process or None if failed
    """
    print_header("Starting API Backend")

    base_dir = Path(__file__).parent
    api_dir = base_dir / 'backend' / 'api'

    if not api_dir.exists():
        print_error(f"API directory not found: {api_dir}")
        return None

    print_info(f"Starting uvicorn on http://0.0.0.0:8000...")

    # Start API in background
    # Set environment variable to disable progress tracking (avoids performance issues)
    env = os.environ.copy()
    env['ENABLE_PROGRESS_TRACKING'] = 'false'

    try:
        proc = subprocess.Popen(
            ['uv', 'run', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'],
            cwd=api_dir,
            env=env,
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
                    print_success("API backend started successfully")
                    return proc
                else:
                    print_warning("API backend started but not responding correctly")
                    return proc
        except Exception:
            print_warning("API backend may still be starting...")
            return proc
    except Exception as e:
        print_error(f"Failed to start API backend: {e}")
        return None


def start_nextjs_frontend() -> Optional[subprocess.Popen]:
    """
    Start the Next.js frontend on port 3000.

    Returns:
        subprocess.Popen: Frontend process or None if failed
    """
    print_header("Starting Next.js Frontend")

    base_dir = Path(__file__).parent
    frontend_dir = base_dir / 'frontend'

    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        return None

    print_info(f"Starting Next.js dev server on http://localhost:3000...")

    # Start Next.js in background
    try:
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
                    print_success("Next.js frontend started successfully")
                    return proc
                else:
                    print_warning("Next.js frontend started but not responding correctly")
                    return proc
        except Exception:
            print_warning("Next.js frontend may still be starting...")
            return proc
    except Exception as e:
        print_error(f"Failed to start Next.js frontend: {e}")
        return None


# ============================================================================
# PHASE 5: STATUS REPORTING
# ============================================================================

def print_final_status(vm_ip: str, arn_status: Dict):
    """
    Print comprehensive status report showing all service URLs and sync status.

    Args:
        vm_ip: External IP address
        arn_status: ARN synchronization status dict
    """
    print_header("Alex Development Environment - Ready!")

    # Service URLs
    print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}API Backend:{Colors.RESET}    http://{vm_ip}:8000")
    print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}API Docs:{Colors.RESET}       http://{vm_ip}:8000/docs")
    print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Next.js:{Colors.RESET}        http://{vm_ip}:3000")

    # ARN Status
    print()
    if arn_status.get("auto_synced"):
        print(f"{Colors.YELLOW}⚠  ARNs were automatically synchronized{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}✓  ARNs verified - in sync{Colors.RESET}")

    # Manual actions needed
    if arn_status.get("actions_needed"):
        print(f"\n{Colors.YELLOW}{Colors.BOLD}MANUAL ACTION REQUIRED:{Colors.RESET}")
        for action in arn_status["actions_needed"]:
            print(f"  {Colors.YELLOW}•{Colors.RESET} {action}")
        print(f"\n{Colors.CYAN}Run:{Colors.RESET} {Colors.BOLD}python3 update_github_secrets.py{Colors.RESET}")

    # Access instructions
    print(f"\n{Colors.CYAN}{'─'*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Access the application:{Colors.RESET}")
    print(f"  Frontend: {Colors.BOLD}http://{vm_ip}:3000{Colors.RESET}")
    print(f"  API Docs: {Colors.BOLD}http://{vm_ip}:8000/docs{Colors.RESET}")

    # Important notes
    print(f"\n{Colors.YELLOW}Note:{Colors.RESET} Make sure ports 3000 and 8000 are open in your firewall")
    print(f"{Colors.RED}Press Ctrl+C to stop all services{Colors.RESET}\n")


def monitor_services(api_proc: subprocess.Popen, frontend_proc: subprocess.Popen):
    """
    Keep services running and handle graceful shutdown.

    Args:
        api_proc: API backend process
        frontend_proc: Frontend process
    """
    try:
        while True:
            # Check if processes are still running
            if api_proc.poll() is not None:
                print_error("API backend stopped unexpectedly")
                break
            if frontend_proc.poll() is not None:
                print_error("Next.js frontend stopped unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print_header("Shutting Down Services")
        print_info("Stopping services gracefully...")

        # Terminate processes
        api_proc.terminate()
        frontend_proc.terminate()
        time.sleep(2)

        # Force kill if still running
        try:
            api_proc.kill()
        except:
            pass
        try:
            frontend_proc.kill()
        except:
            pass

        print_success("All services stopped")


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def main():
    """Main entry point for kb_start.py"""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="KB Start - Master startup script for Alex development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 kb_start.py                    # Start everything (recommended)
  python3 kb_start.py --skip-arn-check  # Skip ARN verification (not recommended)
  python3 kb_start.py --ip-only         # Only update IP, don't start services
  python3 kb_start.py --verify-only     # Only verify ARNs, don't start services
        """
    )
    parser.add_argument(
        "--skip-arn-check",
        action="store_true",
        help="Skip ARN verification (not recommended)"
    )
    parser.add_argument(
        "--ip-only",
        action="store_true",
        help="Only update IP configuration, don't start services"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify ARN synchronization, don't start services"
    )

    args = parser.parse_args()

    print_header("KB Start - Alex Development Environment")

    # PHASE 1: System Checks
    print_info("Running system checks...")

    vm_ip = get_vm_external_ip()
    if not vm_ip:
        print_error("Could not detect VM IP address!")
        sys.exit(1)
    print_success(f"VM IP detected: {Colors.BOLD}{vm_ip}{Colors.RESET}")

    if not check_required_files():
        sys.exit(1)
    print_success("Required configuration files exist")

    # PHASE 2: ARN Synchronization
    arn_status = verify_and_sync_arns(skip_check=args.skip_arn_check)

    # If verify-only mode, exit here
    if args.verify_only:
        print()
        print_success("ARN verification complete")
        sys.exit(0)

    # PHASE 3: IP Configuration
    configure_ip_settings(vm_ip)

    # If ip-only mode, exit here
    if args.ip_only:
        print()
        print_success("IP configuration complete")
        sys.exit(0)

    # PHASE 4: Service Startup
    kill_existing_processes()

    api_proc = start_api_backend()
    if not api_proc:
        print_error("Failed to start API backend. Exiting.")
        sys.exit(1)

    frontend_proc = start_nextjs_frontend()
    if not frontend_proc:
        print_error("Failed to start Next.js frontend. Stopping API backend.")
        api_proc.terminate()
        sys.exit(1)

    # PHASE 5: Status Report
    print_final_status(vm_ip, arn_status)

    # Monitor services
    monitor_services(api_proc, frontend_proc)


if __name__ == '__main__':
    main()
