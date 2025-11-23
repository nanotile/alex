#!/usr/bin/env python3
"""
Create a new Git branch from main
Usage:
    uv run github_new_branch.py  (interactive - will prompt for branch name)
    python github_new_branch.py branch_name  (direct with argument)

Recommended: Use interactive mode with uv run for simplicity
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


def run_git_command(args: list[str], check: bool = True) -> Optional[subprocess.CompletedProcess]:
    """Run a git command and return the result"""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
        if e.stderr:
            print(e.stderr)
        return None


def main():
    """Create a new branch from main"""
    # Get branch name from argument or prompt user
    if len(sys.argv) > 1:
        branch_name = sys.argv[1]
    else:
        branch_name = input(f"{Colors.YELLOW}Enter new branch name: {Colors.NC}").strip()
        if not branch_name:
            print(f"{Colors.RED}Error: Branch name cannot be empty{Colors.NC}")
            sys.exit(1)

    print(f"\n{Colors.BLUE}Creating new branch: {branch_name}{Colors.NC}\n")

    # Step 1: Make sure we're starting from the latest main
    print(f"{Colors.YELLOW}Step 1: Checking out main...{Colors.NC}")
    if run_git_command(['checkout', 'main']) is None:
        sys.exit(1)

    print(f"\n{Colors.YELLOW}Step 2: Pulling latest changes from origin/main...{Colors.NC}")
    if run_git_command(['pull', 'origin', 'main']) is None:
        sys.exit(1)

    # Step 2: Create and switch to the new branch
    print(f"\n{Colors.YELLOW}Step 3: Creating new branch '{branch_name}'...{Colors.NC}")
    if run_git_command(['checkout', '-b', branch_name]) is None:
        sys.exit(1)

    # Step 3: Push the new branch to GitHub
    print(f"\n{Colors.YELLOW}Step 4: Pushing branch to GitHub...{Colors.NC}")
    if run_git_command(['push', '-u', 'origin', branch_name]) is None:
        sys.exit(1)

    print(f"\n{Colors.GREEN}SUCCESS! New branch '{branch_name}' created and pushed to GitHub.{Colors.NC}")


if __name__ == "__main__":
    main()
