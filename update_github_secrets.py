#!/usr/bin/env python3
"""
GitHub Secrets Update Helper for Alex Project

Guides you through updating GitHub Actions secrets with current ARN values.
Shows formatted ARN values for easy copy-paste into GitHub UI.

Usage:
    python3 update_github_secrets.py              # Interactive guide
    python3 update_github_secrets.py --show-only  # Just show ARNs
    python3 update_github_secrets.py --gh-cli     # Use GitHub CLI (if available)

Author: KB (Kent Benson)
Project: Alex - AI in Production
"""

import json
import subprocess
import sys
import shutil
import argparse
from pathlib import Path
from typing import Dict, Optional

# ANSI colors
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")


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


def read_terraform_arns() -> Optional[Dict[str, str]]:
    """
    Read current ARN values from terraform outputs.

    Returns:
        dict: {"cluster_arn": "...", "secret_arn": "..."}  or None if failed
    """
    project_root = Path(__file__).parent
    database_tf_dir = project_root / "terraform/5_database"

    if not database_tf_dir.exists():
        print_error(f"Database terraform directory not found: {database_tf_dir}")
        return None

    try:
        # Run terraform output to get ARNs
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=database_tf_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print_error("Failed to read terraform outputs")
            print_info(f"Run: cd {database_tf_dir} && terraform output")
            return None

        outputs = json.loads(result.stdout)

        # Extract ARN values (try both naming conventions)
        cluster_arn = (outputs.get("aurora_cluster_arn", {}).get("value") or
                      outputs.get("cluster_arn", {}).get("value"))
        secret_arn = (outputs.get("aurora_secret_arn", {}).get("value") or
                     outputs.get("secret_arn", {}).get("value"))

        if not cluster_arn or not secret_arn:
            print_error("Could not find cluster ARN or secret ARN in terraform outputs")
            print_info("Available outputs: " + ", ".join(outputs.keys()))
            return None

        return {
            "cluster_arn": cluster_arn,
            "secret_arn": secret_arn
        }

    except subprocess.TimeoutExpired:
        print_error("Terraform command timed out")
        return None
    except json.JSONDecodeError:
        print_error("Invalid JSON from terraform output")
        return None
    except FileNotFoundError:
        print_error("Terraform not found. Install terraform: https://www.terraform.io/downloads")
        return None
    except Exception as e:
        print_error(f"Failed to read terraform outputs: {e}")
        return None


def get_github_repo_info() -> Optional[Dict[str, str]]:
    """
    Get GitHub repository information from git remote.

    Returns:
        dict: {"owner": "...", "repo": "..."} or None if failed
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return None

        # Parse GitHub URL (supports both HTTPS and SSH)
        url = result.stdout.strip()

        # Handle SSH format: git@github.com:user/repo.git
        if url.startswith("git@github.com:"):
            parts = url.replace("git@github.com:", "").replace(".git", "").split("/")
            if len(parts) == 2:
                return {"owner": parts[0], "repo": parts[1]}

        # Handle HTTPS format: https://github.com/user/repo.git
        if "github.com/" in url:
            parts = url.split("github.com/")[1].replace(".git", "").split("/")
            if len(parts) == 2:
                return {"owner": parts[0], "repo": parts[1]}

        return None

    except Exception:
        return None


def update_via_gh_cli(arns: Dict[str, str], repo_info: Dict[str, str]) -> bool:
    """
    Update GitHub secrets using gh CLI.

    Args:
        arns: Dictionary with cluster_arn and secret_arn
        repo_info: Dictionary with owner and repo

    Returns:
        bool: True if successful
    """
    repo_full_name = f"{repo_info['owner']}/{repo_info['repo']}"

    print()
    print_info(f"Updating secrets for repository: {repo_full_name}")

    success = True

    # Update AURORA_CLUSTER_ARN
    print_info("Setting AURORA_CLUSTER_ARN...")
    try:
        result = subprocess.run(
            ["gh", "secret", "set", "AURORA_CLUSTER_ARN", "--body", arns["cluster_arn"], "--repo", repo_full_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print_success("AURORA_CLUSTER_ARN updated")
        else:
            print_error(f"Failed to update AURORA_CLUSTER_ARN: {result.stderr}")
            success = False
    except Exception as e:
        print_error(f"Failed to update AURORA_CLUSTER_ARN: {e}")
        success = False

    # Update AURORA_SECRET_ARN
    print_info("Setting AURORA_SECRET_ARN...")
    try:
        result = subprocess.run(
            ["gh", "secret", "set", "AURORA_SECRET_ARN", "--body", arns["secret_arn"], "--repo", repo_full_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print_success("AURORA_SECRET_ARN updated")
        else:
            print_error(f"Failed to update AURORA_SECRET_ARN: {result.stderr}")
            success = False
    except Exception as e:
        print_error(f"Failed to update AURORA_SECRET_ARN: {e}")
        success = False

    return success


def main():
    """Main entry point for update_github_secrets.py"""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="GitHub Secrets Update Helper for Alex Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 update_github_secrets.py              # Interactive guide (default)
  python3 update_github_secrets.py --show-only  # Just show ARN values
  python3 update_github_secrets.py --gh-cli     # Use GitHub CLI automation
        """
    )
    parser.add_argument(
        "--show-only",
        action="store_true",
        help="Only show ARN values, don't prompt for updates"
    )
    parser.add_argument(
        "--gh-cli",
        action="store_true",
        help="Use GitHub CLI to update automatically (requires 'gh' installed and authenticated)"
    )

    args = parser.parse_args()

    print_header("GitHub Actions Secrets Update Guide")

    # Read ARNs from terraform
    print_info("Reading current ARN values from terraform outputs...")
    arns = read_terraform_arns()

    if not arns:
        print_error("Could not read ARN values from terraform")
        print_info("Ensure database is deployed: cd terraform/5_database && terraform apply")
        sys.exit(1)

    # Display ARN values
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}📋 Current ARN Values{Colors.RESET}")
    print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}")
    print()
    print(f"{Colors.BOLD}AURORA_CLUSTER_ARN:{Colors.RESET}")
    print(f"  {Colors.GREEN}{arns['cluster_arn']}{Colors.RESET}")
    print()
    print(f"{Colors.BOLD}AURORA_SECRET_ARN:{Colors.RESET}")
    print(f"  {Colors.GREEN}{arns['secret_arn']}{Colors.RESET}")
    print()

    # If show-only mode, exit here
    if args.show_only:
        print_info("ARN values displayed above")
        sys.exit(0)

    # Get GitHub repo info
    repo_info = get_github_repo_info()

    if repo_info:
        github_url = f"https://github.com/{repo_info['owner']}/{repo_info['repo']}/settings/secrets/actions"
    else:
        github_url = "https://github.com/YOUR_USER/YOUR_REPO/settings/secrets/actions"

    # Check if gh CLI is available and try automated update
    if args.gh_cli or (shutil.which("gh") and not args.show_only):
        if not shutil.which("gh"):
            print_warning("GitHub CLI ('gh') not found")
            print_info("Install gh: https://cli.github.com/")
        elif not repo_info:
            print_warning("Could not detect GitHub repository information")
        else:
            if args.gh_cli:
                # Force gh CLI mode
                print()
                print_info("Using GitHub CLI to update secrets automatically...")
                success = update_via_gh_cli(arns, repo_info)
                if success:
                    print()
                    print_success("GitHub secrets updated successfully!")
                    print_info("Deployment tests will now use the new ARNs")
                else:
                    print_error("Failed to update some secrets via gh CLI")
                    print_info("You can update manually using the values above")
                sys.exit(0 if success else 1)
            else:
                # Offer gh CLI as option
                print(f"{Colors.MAGENTA}💡 GitHub CLI detected!{Colors.RESET}")
                print()
                response = input(f"Use 'gh' to update secrets automatically? (y/n): ").strip().lower()
                if response == 'y':
                    print()
                    success = update_via_gh_cli(arns, repo_info)
                    if success:
                        print()
                        print_success("GitHub secrets updated successfully!")
                        print_info("Deployment tests will now use the new ARNs")
                        sys.exit(0)
                    else:
                        print_error("Failed to update some secrets via gh CLI")
                        print_info("Continuing with manual instructions...")
                        print()

    # Manual update instructions
    print(f"{Colors.BOLD}{Colors.YELLOW}📝 Manual Update Steps{Colors.RESET}")
    print(f"{Colors.YELLOW}{'─'*70}{Colors.RESET}")
    print()
    print(f"1. Go to GitHub repository settings:")
    print(f"   {Colors.CYAN}{github_url}{Colors.RESET}")
    print()
    print(f"2. Update {Colors.BOLD}AURORA_CLUSTER_ARN{Colors.RESET}:")
    print(f"   • Click 'Edit' or 'Update' next to AURORA_CLUSTER_ARN")
    print(f"   • Paste the value shown above")
    print(f"   • Click 'Update secret'")
    print()
    print(f"3. Update {Colors.BOLD}AURORA_SECRET_ARN{Colors.RESET}:")
    print(f"   • Click 'Edit' or 'Update' next to AURORA_SECRET_ARN")
    print(f"   • Paste the value shown above")
    print(f"   • Click 'Update secret'")
    print()
    print(f"{Colors.GREEN}✅ Once updated:{Colors.RESET}")
    print(f"  • GitHub Actions deployment tests will use the new ARNs")
    print(f"  • CI/CD pipeline will be able to access the database")
    print(f"  • No more 'AccessDenied' errors in deployment tests")
    print()


if __name__ == '__main__':
    main()
