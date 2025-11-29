#!/usr/bin/env python3
"""
KB Stop - Cleanly stop all Alex development services

Stops API backend and Next.js frontend, then optionally verifies ARN sync status.

Usage:
    python3 kb_stop.py              # Stop all services
    python3 kb_stop.py --no-verify  # Skip ARN verification

Author: KB (Kent Benson)
Project: Alex - AI in Production
"""

import subprocess
import sys
import argparse
from pathlib import Path

# ANSI colors
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ{Colors.RESET} {text}")


def kill_port(port: int, service_name: str) -> bool:
    """
    Kill processes on a specific port.

    Args:
        port: Port number
        service_name: Human-readable service name

    Returns:
        bool: True if process was killed, False if none found
    """
    try:
        # Find and kill processes on the port
        result = subprocess.run(
            f"lsof -ti:{port} | xargs kill -9 2>/dev/null",
            shell=True,
            capture_output=True
        )
        if result.returncode == 0:
            print_success(f"Stopped {service_name} (port {port})")
            return True
        else:
            print_warning(f"No {service_name} found on port {port}")
            return False
    except Exception as e:
        print_warning(f"Could not stop {service_name}: {e}")
        return False


def verify_arn_status():
    """Run ARN verification to show current sync status."""
    print_header("ARN Synchronization Status")

    project_root = Path(__file__).parent
    verify_script = project_root / "scripts" / "verify_arns.py"

    if not verify_script.exists():
        print_warning("verify_arns.py not found, skipping ARN check")
        return

    print_info("Checking ARN synchronization status...")

    try:
        result = subprocess.run(
            ["python3", str(verify_script)],
            capture_output=True,
            text=True,
            timeout=30
        )

        # The verify script prints its own output
        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            print()
            print_success("ARNs are in sync")
        elif result.returncode == 2:
            print()
            print_warning("ARNs are OUT OF SYNC")
            print_info("Run before next startup: python3 kb_start.py")
            print_info("Or sync manually: uv run scripts/sync_arns.py")
        else:
            print_warning("Could not verify ARN status")

    except subprocess.TimeoutExpired:
        print_warning("ARN verification timed out")
    except Exception as e:
        print_warning(f"ARN verification failed: {e}")


def main():
    """Main entry point for kb_stop.py"""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="KB Stop - Stop all Alex development services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 kb_stop.py              # Stop all services (default)
  python3 kb_stop.py --no-verify  # Skip ARN verification
        """
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip ARN synchronization verification"
    )

    args = parser.parse_args()

    print_header("KB Stop - Shutting Down Alex Services")

    # Kill API backend (port 8000)
    api_stopped = kill_port(8000, "API Backend")

    # Kill Next.js frontend (port 3000)
    frontend_stopped = kill_port(3000, "Next.js Frontend")

    # Verify ARN status (unless skipped)
    if not args.no_verify:
        print()
        verify_arn_status()

    # Summary
    print()
    print_header("Shutdown Complete")

    if api_stopped or frontend_stopped:
        print_success("All services stopped successfully")
    else:
        print_info("No services were running")

    print()
    print_info("To restart: python3 kb_start.py")
    print()


if __name__ == '__main__':
    main()
