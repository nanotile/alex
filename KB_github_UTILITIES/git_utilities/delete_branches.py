#!/usr/bin/env python3
"""
Delete Git Branches (Local and Remote)
Displays all branches and allows selective deletion with safety confirmations.

Usage:
  uv run delete_branches.py  (interactive mode)
  python delete_branches.py  (interactive mode)

Features:
- Shows all local and remote branches
- Prevents deletion of current branch
- Prevents deletion of main/master
- Offers to delete both local and remote
- Confirmation prompts for safety
"""

import subprocess
import sys
from typing import List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


def run_git_command(args: List[str], check: bool = False, show_output: bool = True) -> Optional[subprocess.CompletedProcess]:
    """Run a git command and return the result"""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            check=check
        )
        if show_output and result.returncode == 0:
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
        return result
    except subprocess.CalledProcessError as e:
        if show_output:
            print(f"{Colors.RED}Error: {e}{Colors.NC}")
            if e.stderr:
                print(e.stderr)
        return None


def get_current_branch() -> Optional[str]:
    """Get the current branch name"""
    result = run_git_command(['branch', '--show-current'], show_output=False)
    return result.stdout.strip() if result and result.returncode == 0 else None


def get_all_branches() -> Tuple[List[str], List[str]]:
    """Get all local and remote branches"""
    print(f"{Colors.BLUE}Fetching latest branches from remote...{Colors.NC}")
    run_git_command(['fetch', '--all', '--prune'], show_output=False)

    # Get local branches
    result = run_git_command(['branch'], show_output=False)
    local_branches = []
    if result and result.returncode == 0:
        for line in result.stdout.split('\n'):
            branch = line.replace('*', '').strip()
            if branch:
                local_branches.append(branch)

    # Get remote branches
    result = run_git_command(['branch', '-r'], show_output=False)
    remote_branches = []
    if result and result.returncode == 0:
        for line in result.stdout.split('\n'):
            branch = line.strip()
            if branch and 'HEAD' not in branch:
                # Remove 'origin/' prefix for display
                branch = branch.replace('origin/', '')
                remote_branches.append(branch)

    return local_branches, remote_branches


def display_branches(local_branches: List[str], remote_branches: List[str], current_branch: str):
    """Display all branches with status indicators"""
    print(f"\n{Colors.GREEN}=== Branch Status ==={Colors.NC}\n")
    print(f"{Colors.CYAN}Current branch: {current_branch}{Colors.NC}\n")

    # Combine and deduplicate
    all_branches = set(local_branches + remote_branches)
    all_branches = sorted(list(all_branches))

    print(f"{Colors.YELLOW}Branch List:{Colors.NC}")
    print(f"{'#':<4} {'Branch Name':<40} {'Location':<20}")
    print("-" * 70)

    for i, branch in enumerate(all_branches, 1):
        is_local = branch in local_branches
        is_remote = branch in remote_branches
        is_current = branch == current_branch
        is_protected = branch in ['main', 'master']

        # Location indicator
        if is_local and is_remote:
            location = "Local + Remote"
        elif is_local:
            location = "Local only"
        elif is_remote:
            location = "Remote only"
        else:
            location = "Unknown"

        # Status indicator
        status = ""
        if is_current:
            status = f"{Colors.CYAN}(current){Colors.NC}"
        elif is_protected:
            status = f"{Colors.RED}(protected){Colors.NC}"

        print(f"{i:<4} {branch:<40} {location:<20} {status}")

    print()


def confirm_action(message: str) -> bool:
    """Ask user for confirmation"""
    response = input(f"{message} (y/n): ").strip().lower()
    return response in ['y', 'yes']


def delete_branch(branch: str, current_branch: str, local_branches: List[str], remote_branches: List[str]):
    """Delete a branch (local and/or remote)"""
    # Safety checks
    if branch == current_branch:
        print(f"{Colors.RED}Error: Cannot delete the current branch '{branch}'{Colors.NC}")
        print(f"{Colors.YELLOW}You are currently on this branch.{Colors.NC}")

        # Offer to switch to main
        if confirm_action(f"Would you like to switch to 'main' first?"):
            print(f"\n{Colors.YELLOW}Switching to main...{Colors.NC}")
            result = run_git_command(['checkout', 'main'], show_output=True)
            if result and result.returncode == 0:
                print(f"{Colors.GREEN}✓ Switched to main{Colors.NC}")
                print(f"\n{Colors.YELLOW}Now attempting to delete '{branch}'...{Colors.NC}")
                # Update current_branch for the check
                current_branch = 'main'
            else:
                print(f"{Colors.RED}✗ Failed to switch to main{Colors.NC}")
                return False
        else:
            return False

    if branch in ['main', 'master']:
        print(f"{Colors.RED}Error: Cannot delete protected branch '{branch}'{Colors.NC}")
        return False

    is_local = branch in local_branches
    is_remote = branch in remote_branches

    if not is_local and not is_remote:
        print(f"{Colors.RED}Error: Branch '{branch}' not found{Colors.NC}")
        return False

    # Show what will be deleted
    print(f"\n{Colors.YELLOW}Branch to delete: {branch}{Colors.NC}")
    if is_local:
        print(f"  ✓ Local branch exists")
    if is_remote:
        print(f"  ✓ Remote branch exists")

    # Confirm deletion
    if not confirm_action(f"\n{Colors.RED}Are you sure you want to delete '{branch}'?{Colors.NC}"):
        print("Deletion cancelled.")
        return False

    success = True

    # Delete local branch
    if is_local:
        print(f"\n{Colors.YELLOW}Deleting local branch '{branch}'...{Colors.NC}")
        result = run_git_command(['branch', '-D', branch], show_output=False)
        if result and result.returncode == 0:
            print(f"{Colors.GREEN}✓ Local branch '{branch}' deleted{Colors.NC}")
        else:
            print(f"{Colors.RED}✗ Failed to delete local branch '{branch}'{Colors.NC}")
            success = False

    # Delete remote branch
    if is_remote:
        print(f"\n{Colors.YELLOW}Deleting remote branch '{branch}'...{Colors.NC}")
        result = run_git_command(['push', 'origin', '--delete', branch], show_output=False)
        if result and result.returncode == 0:
            print(f"{Colors.GREEN}✓ Remote branch '{branch}' deleted from GitHub{Colors.NC}")
        else:
            print(f"{Colors.RED}✗ Failed to delete remote branch '{branch}'{Colors.NC}")
            success = False

    if success:
        print(f"\n{Colors.GREEN}✓✓✓ Branch '{branch}' successfully deleted!{Colors.NC}")
        print(f"{Colors.CYAN}(Branch list will refresh on next display){Colors.NC}")

    return success


def delete_multiple_branches():
    """Interactive mode for deleting multiple branches"""
    while True:
        # Get current state
        current_branch = get_current_branch()
        if not current_branch:
            print(f"{Colors.RED}Error: Could not determine current branch{Colors.NC}")
            return

        local_branches, remote_branches = get_all_branches()
        all_branches = sorted(list(set(local_branches + remote_branches)))

        # Display branches
        display_branches(local_branches, remote_branches, current_branch)

        # Get user input
        print(f"{Colors.YELLOW}Options:{Colors.NC}")
        print("1) Enter branch number to delete")
        print("2) Enter branch name to delete")
        print("3) Exit")
        print()

        choice = input("Select option (1-3): ").strip()

        if choice == "1":
            try:
                branch_num = int(input("Enter branch number: "))
                if 1 <= branch_num <= len(all_branches):
                    branch = all_branches[branch_num - 1]
                    delete_branch(branch, current_branch, local_branches, remote_branches)
                else:
                    print(f"{Colors.RED}Invalid branch number{Colors.NC}")
            except ValueError:
                print(f"{Colors.RED}Invalid input{Colors.NC}")

        elif choice == "2":
            branch = input("Enter branch name: ").strip()
            delete_branch(branch, current_branch, local_branches, remote_branches)

        elif choice == "3":
            print(f"\n{Colors.BLUE}Goodbye!{Colors.NC}")
            break

        else:
            print(f"{Colors.RED}Invalid option{Colors.NC}")

        print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}\n")


def main():
    """Main function"""
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}")
    print(f"{Colors.GREEN}Git Branch Deletion Tool{Colors.NC}")
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")

    delete_multiple_branches()


if __name__ == "__main__":
    main()
