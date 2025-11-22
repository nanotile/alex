#!/usr/bin/env python3
"""
Stop Alex development servers.
Kills both API backend and Next.js frontend processes.
"""

import subprocess
import sys

# ANSI colors
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

def kill_port(port, service_name):
    """Kill processes on a specific port."""
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

def main():
    """Main entry point."""
    print_header("Stopping Alex Development Servers")

    # Kill API backend (port 8000)
    api_stopped = kill_port(8000, "API Backend")

    # Kill Next.js frontend (port 3000)
    frontend_stopped = kill_port(3000, "Next.js Frontend")

    # Summary
    print()
    if api_stopped or frontend_stopped:
        print_success("All services stopped successfully")
    else:
        print_warning("No services were running")

    print()

if __name__ == '__main__':
    main()
