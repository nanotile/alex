#!/usr/bin/env python3
"""
BURN IT DOWN & START NEW
Use this to discard a broken feature branch and start a fresh one from clean main.

Usage:
  uv run burn_it_down_start_new.py  (interactive mode - will prompt)
  python burn_it_down_start_new.py old_branch new_branch  (direct with arguments)

Recommended: Use interactive mode with uv run for simplicity

Reference: https://gemini.google.com/app/76918706123e0583
"""

import subprocess
import sys
from typing import Optional


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'


def run_git_command(args: list[str], check: bool = False, show_output: bool = True) -> Optional[subprocess.CompletedProcess]:
    """Run a git command and return the result"""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            check=check
        )
        if show_output:
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr and result.returncode == 0:
                print(result.stderr.strip())
        return result
    except subprocess.CalledProcessError as e:
        if show_output:
            print(f"{Colors.RED}Error: {e}{Colors.NC}")
            if e.stderr:
                print(e.stderr)
        return None


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default value"""
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    return input(f"{prompt}: ").strip()


def confirm_action(message: str) -> bool:
    """Ask user for confirmation"""
    response = input(f"{message} (y/n): ").strip().lower()
    return response in ['y', 'yes']


def main():
    """Main function to burn down old branch and create new one"""
    print(f"{Colors.RED}{'='*60}{Colors.NC}")
    print(f"{Colors.RED}BURN IT DOWN & START NEW{Colors.NC}")
    print(f"{Colors.RED}Use this to discard a broken feature branch{Colors.NC}")
    print(f"{Colors.RED}and start a fresh one from clean main.{Colors.NC}")
    print(f"{Colors.RED}{'='*60}{Colors.NC}\n")

    # Step 1: Get Arguments (or prompt if missing)
    old_branch = sys.argv[1] if len(sys.argv) > 1 else ""
    new_branch = sys.argv[2] if len(sys.argv) > 2 else ""

    if not old_branch:
        old_branch = get_input("Enter the name of the BROKEN branch to delete")

    if not new_branch:
        new_branch = get_input("Enter the name of the NEW branch to create")

    # Step 2: Confirmation Safety Check
    print(f"\n{Colors.RED}WARNING: This will force-delete '{old_branch}' locally and on GitHub.{Colors.NC}")
    if not confirm_action("Are you sure you want to proceed?"):
        print("Aborted.")
        sys.exit(0)

    # Step 3: Switch to Main and clean up
    print(f"\n{Colors.YELLOW}Step 1: Switching to Main and cleaning up...{Colors.NC}")
    if run_git_command(['checkout', 'main'], check=True) is None:
        sys.exit(1)

    if run_git_command(['fetch', 'origin'], check=True) is None:
        sys.exit(1)

    # Hard reset main to match GitHub exactly
    if run_git_command(['reset', '--hard', 'origin/main'], check=True) is None:
        sys.exit(1)

    # Step 4: Delete the old branch
    print(f"\n{Colors.YELLOW}Step 2: Deleting the old branch ('{old_branch}')...{Colors.NC}")

    # Delete local copy (force)
    result = run_git_command(['branch', '-D', old_branch], show_output=False)
    if result and result.returncode == 0:
        print(f"✓ Local branch '{old_branch}' deleted")
    else:
        print(f"• Local branch '{old_branch}' not found (skipping)")

    # Delete remote copy
    result = run_git_command(['push', 'origin', '--delete', old_branch], show_output=False)
    if result and result.returncode == 0:
        print(f"✓ Remote branch '{old_branch}' deleted from GitHub")
    else:
        print(f"• Remote branch '{old_branch}' not found on GitHub (skipping)")

    # Step 5: Create fresh branch
    print(f"\n{Colors.YELLOW}Step 3: Creating fresh branch ('{new_branch}')...{Colors.NC}")
    if run_git_command(['checkout', '-b', new_branch], check=True) is None:
        sys.exit(1)

    # Step 6: Push to GitHub
    print(f"\n{Colors.YELLOW}Step 4: Pushing to GitHub...{Colors.NC}")
    if run_git_command(['push', '-u', 'origin', new_branch], check=True) is None:
        sys.exit(1)

    # Success message
    print(f"\n{Colors.GREEN}{'='*60}{Colors.NC}")
    print(f"{Colors.GREEN}DONE! You are now on '{new_branch}' which is a clean copy of main.{Colors.NC}")
    print(f"{Colors.GREEN}{'='*60}{Colors.NC}")


if __name__ == "__main__":
    main()
