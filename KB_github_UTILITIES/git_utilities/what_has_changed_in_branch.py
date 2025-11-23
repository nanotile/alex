#!/usr/bin/env python3
"""
Git Branch Comparison Tool
Compares changes between branches using various methods
"""

import subprocess
import sys
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color


def run_git_command(args: List[str], capture_output: bool = True) -> Optional[str]:
    """Run a git command and return output"""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error running git command: {e}{Colors.NC}")
        return None


def get_branches() -> List[str]:
    """Get all branches (local and remote)"""
    print(f"{Colors.BLUE}Fetching latest branches from remote...{Colors.NC}")
    run_git_command(['fetch', '--all', '--quiet'])

    # Get all branches
    output = run_git_command(['branch', '-a'])
    if not output:
        return []

    # Parse and deduplicate branches
    branches = set()
    for line in output.split('\n'):
        # Remove markers and whitespace
        branch = line.replace('*', '').strip()
        # Remove 'remotes/origin/' prefix
        if branch.startswith('remotes/origin/'):
            branch = branch.replace('remotes/origin/', '')
        # Skip HEAD pointer
        if 'HEAD' not in branch and branch:
            branches.add(branch)

    return sorted(list(branches))


def select_branch(branches: List[str]) -> Optional[str]:
    """Display branches and let user select one"""
    print(f"\n{Colors.YELLOW}Available branches:{Colors.NC}")
    for i, branch in enumerate(branches, 1):
        print(f"{i:3d}) {branch}")

    try:
        choice = input(f"\n{Colors.YELLOW}Enter branch number to compare against: {Colors.NC}")
        branch_num = int(choice)

        if 1 <= branch_num <= len(branches):
            return branches[branch_num - 1]
        else:
            print(f"{Colors.RED}Invalid branch number!{Colors.NC}")
            return None
    except (ValueError, KeyboardInterrupt):
        print(f"\n{Colors.RED}Invalid input!{Colors.NC}")
        return None


def get_current_branch() -> Optional[str]:
    """Get the current branch name"""
    return run_git_command(['branch', '--show-current'])


def show_menu() -> Optional[int]:
    """Display comparison method menu and get user choice"""
    print(f"\n{Colors.YELLOW}Select comparison method:{Colors.NC}")
    print("1) Full code diff (git diff)")
    print("2) File list with status (git diff --name-status)")
    print("3) Commit history (git log)")
    print("4) Summary statistics (git diff --stat)")
    print("5) Compare specific file")
    print("6) Show all methods")
    print()

    try:
        choice = input("Select option (1-6): ")
        option = int(choice)

        if 1 <= option <= 6:
            return option
        else:
            print(f"{Colors.RED}Invalid option!{Colors.NC}")
            return None
    except (ValueError, KeyboardInterrupt):
        print(f"\n{Colors.RED}Invalid input!{Colors.NC}")
        return None


def show_full_diff(selected_branch: str):
    """Show full code differences"""
    print(f"\n{Colors.GREEN}Full code differences:{Colors.NC}\n")
    subprocess.run(['git', 'diff', selected_branch])


def show_file_status(selected_branch: str):
    """Show files changed with status"""
    print(f"\n{Colors.GREEN}Files changed:{Colors.NC}\n")
    subprocess.run(['git', 'diff', '--name-status', selected_branch])


def show_commit_history(selected_branch: str, current_branch: str):
    """Show commit history"""
    print(f"\n{Colors.GREEN}Commits in {current_branch} not in {selected_branch}:{Colors.NC}\n")
    subprocess.run(['git', 'log', f'{selected_branch}..HEAD', '--oneline', '--graph', '--decorate'])


def show_summary_stats(selected_branch: str):
    """Show summary statistics"""
    print(f"\n{Colors.GREEN}Summary statistics:{Colors.NC}\n")
    subprocess.run(['git', 'diff', '--stat', selected_branch])


def show_file_diff(selected_branch: str):
    """Show diff for a specific file"""
    filepath = input(f"{Colors.YELLOW}Enter file path: {Colors.NC}")
    print(f"\n{Colors.GREEN}Differences in {filepath}:{Colors.NC}\n")
    subprocess.run(['git', 'diff', selected_branch, '--', filepath])


def show_all_methods(selected_branch: str, current_branch: str):
    """Show all comparison methods"""
    print(f"\n{Colors.GREEN}1. File list with status:{Colors.NC}\n")
    subprocess.run(['git', 'diff', '--name-status', selected_branch])

    print(f"\n{Colors.GREEN}2. Summary statistics:{Colors.NC}\n")
    subprocess.run(['git', 'diff', '--stat', selected_branch])

    print(f"\n{Colors.GREEN}3. Commit history:{Colors.NC}\n")
    subprocess.run(['git', 'log', f'{selected_branch}..HEAD', '--oneline', '--graph', '--decorate'])

    print(f"\n{Colors.GREEN}4. Full code diff (showing first 50 lines):{Colors.NC}\n")
    result = subprocess.run(
        ['git', 'diff', selected_branch],
        capture_output=True,
        text=True
    )
    lines = result.stdout.split('\n')[:50]
    print('\n'.join(lines))
    print(f"\n{Colors.YELLOW}(Full diff truncated - use option 1 to see all){Colors.NC}")


def show_next_action_menu() -> Optional[str]:
    """Show menu for what to do next"""
    print(f"\n{Colors.YELLOW}What would you like to do next?{Colors.NC}")
    print("1) Run another comparison method")
    print("2) Compare against a different branch")
    print("3) Exit")
    print()

    try:
        choice = input("Select option (1-3): ")
        option = int(choice)

        if option == 1:
            return "compare"
        elif option == 2:
            return "new_branch"
        elif option == 3:
            return "exit"
        else:
            print(f"{Colors.RED}Invalid option!{Colors.NC}")
            return None
    except (ValueError, KeyboardInterrupt):
        print(f"\n{Colors.RED}Invalid input!{Colors.NC}")
        return None


def main():
    """Main function"""
    print(f"{Colors.GREEN}=== Git Branch Comparison Tool ==={Colors.NC}\n")

    # Get branches once
    branches = get_branches()
    if not branches:
        print(f"{Colors.RED}No branches found!{Colors.NC}")
        sys.exit(1)

    # Get current branch
    current_branch = get_current_branch()

    # Main loop
    selected_branch = None
    while True:
        # Select branch if not already selected
        if selected_branch is None:
            selected_branch = select_branch(branches)
            if not selected_branch:
                sys.exit(1)

            print(f"{Colors.GREEN}Selected branch: {selected_branch}{Colors.NC}\n")
            if current_branch:
                print(f"{Colors.BLUE}Current branch: {current_branch}{Colors.NC}\n")

        # Show menu and get choice
        option = show_menu()
        if not option:
            sys.exit(1)

        print(f"\n{Colors.GREEN}======================================{Colors.NC}")

        # Execute selected option
        if option == 1:
            show_full_diff(selected_branch)
        elif option == 2:
            show_file_status(selected_branch)
        elif option == 3:
            show_commit_history(selected_branch, current_branch)
        elif option == 4:
            show_summary_stats(selected_branch)
        elif option == 5:
            show_file_diff(selected_branch)
        elif option == 6:
            show_all_methods(selected_branch, current_branch)

        print(f"\n{Colors.GREEN}======================================{Colors.NC}")

        # Ask what to do next
        next_action = show_next_action_menu()

        if next_action == "compare":
            # Continue loop with same branch
            print()
            continue
        elif next_action == "new_branch":
            # Reset selected_branch to trigger new selection
            selected_branch = None
            print()
            continue
        elif next_action == "exit":
            print(f"\n{Colors.BLUE}Goodbye!{Colors.NC}")
            break
        else:
            # Invalid input, ask again
            continue


if __name__ == "__main__":
    main()
