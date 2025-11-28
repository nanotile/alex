"""
ARN Synchronization Script for Alex Project

Automatically syncs ARNs from terraform outputs to configuration files.
Eliminates manual copy-paste errors when infrastructure is recreated.

Usage:
    uv run scripts/sync_arns.py              # Interactive mode (prompts for confirmation)
    uv run scripts/sync_arns.py --auto       # Automatic sync (skip confirmation)
    uv run scripts/sync_arns.py --dry-run    # Preview changes without modifying files
    uv run scripts/sync_arns.py --verify     # Alias for verify_arns.py

Exit Codes:
    0: Success, ARNs synced successfully
    1: Critical failure, deployment should not continue
    2: Verification mode - ARNs out of sync
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil
from datetime import datetime
import re


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ARNSyncManager:
    """Manages synchronization of ARNs from terraform outputs to configuration files"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.terraform_dirs = {
            "database": project_root / "terraform/5_database",
            "agents": project_root / "terraform/6_agents",
            "ingestion": project_root / "terraform/3_ingestion",
        }
        self.config_files = {
            "root_env": project_root / ".env",
            "agents_tfvars": project_root / "terraform/6_agents/terraform.tfvars",
        }
        self.errors = []

    def log_error(self, message: str):
        """Log an error message for later reporting"""
        self.errors.append(message)

    def critical_error(self, message: str, fix_guidance: str):
        """Print critical error and exit with code 1"""
        print(f"\n{Colors.RED}{Colors.BOLD}❌ CRITICAL ERROR{Colors.END}")
        print(f"{Colors.RED}{message}{Colors.END}")
        print(f"\n{Colors.YELLOW}Fix:{Colors.END} {fix_guidance}")
        sys.exit(1)

    def read_terraform_outputs(self, tf_dir: Path) -> Optional[Dict]:
        """Read terraform outputs as JSON"""
        # Check if terraform state exists
        tfstate_path = tf_dir / "terraform.tfstate"
        if not tfstate_path.exists():
            return None

        try:
            result = subprocess.run(
                ["terraform", "output", "-json"],
                cwd=tf_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.critical_error(
                    f"Failed to read terraform outputs from {tf_dir.name}",
                    f"cd {tf_dir} && terraform init && terraform output"
                )

            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            self.critical_error(
                f"Terraform command timed out for {tf_dir.name}",
                f"cd {tf_dir} && terraform init"
            )
        except json.JSONDecodeError as e:
            self.critical_error(
                f"Invalid JSON from terraform output in {tf_dir.name}",
                f"cd {tf_dir} && terraform output -json"
            )
        except FileNotFoundError:
            self.critical_error(
                "Terraform command not found",
                "Install terraform: https://www.terraform.io/downloads"
            )

    def extract_arn_values(self, outputs: Dict) -> Dict[str, str]:
        """Extract ARN values from terraform output JSON"""
        arns = {}
        for key, value in outputs.items():
            if isinstance(value, dict) and "value" in value:
                arns[key] = value["value"]
        return arns

    def validate_arn(self, arn: str, arn_type: str) -> bool:
        """Validate ARN format using regex patterns"""
        patterns = {
            "cluster_arn": r"^arn:aws:rds:[^:]+:\d+:cluster:.+$",
            "secret_arn": r"^arn:aws:secretsmanager:[^:]+:\d+:secret:.+$",
            "aurora_cluster_arn": r"^arn:aws:rds:[^:]+:\d+:cluster:.+$",
            "aurora_secret_arn": r"^arn:aws:secretsmanager:[^:]+:\d+:secret:.+$",
        }

        pattern = patterns.get(arn_type)
        if not pattern:
            return True  # Unknown type, skip validation

        if not re.match(pattern, arn):
            self.critical_error(
                f"Invalid ARN format for {arn_type}: {arn}",
                f"Check terraform outputs for correct format"
            )

        return True

    def detect_arn_changes(self) -> Dict[str, Dict[str, str]]:
        """Detect ARNs from all deployed terraform modules"""
        changes = {}

        print(f"\n{Colors.CYAN}📋 Detecting ARNs from terraform outputs...{Colors.END}")

        for name, tf_dir in self.terraform_dirs.items():
            if not tf_dir.exists():
                print(f"  {Colors.YELLOW}⚠{Colors.END}  {name}: directory not found, skipping")
                continue

            outputs = self.read_terraform_outputs(tf_dir)
            if outputs:
                arns = self.extract_arn_values(outputs)
                if arns:
                    changes[name] = arns
                    print(f"  {Colors.GREEN}✓{Colors.END}  {name}: {len(arns)} ARN(s) found")
                else:
                    print(f"  {Colors.YELLOW}⚠{Colors.END}  {name}: no ARNs in outputs")
            else:
                print(f"  {Colors.YELLOW}⚠{Colors.END}  {name}: not deployed (no terraform.tfstate)")

        # Validate critical ARNs
        if "database" in changes:
            for key in ["cluster_arn", "secret_arn"]:
                if key in changes["database"]:
                    self.validate_arn(changes["database"][key], key)

        return changes

    def backup_file(self, file_path: Path) -> Optional[Path]:
        """Create timestamped backup of config file"""
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.name}.backup_{timestamp}"

        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.critical_error(
                f"Failed to create backup of {file_path}",
                f"Check file permissions: ls -la {file_path}"
            )

    def update_env_file(self, arns: Dict[str, Dict[str, str]], dry_run: bool = False) -> bool:
        """Update .env file with new ARNs"""
        env_path = self.config_files["root_env"]

        if not env_path.exists():
            # Create from example if exists
            example_path = self.project_root / ".env.example"
            if example_path.exists():
                shutil.copy2(example_path, env_path)
            else:
                self.critical_error(
                    f".env file not found and no .env.example to copy from",
                    f"Create .env file manually or from template"
                )

        # Read current content
        try:
            lines = env_path.read_text().splitlines()
        except PermissionError:
            self.critical_error(
                f"Cannot read {env_path}. Permission denied.",
                f"Check file permissions: ls -la {env_path}"
            )

        # Track changes
        updated_lines = []
        changes_made = False

        for line in lines:
            updated = False

            # Database ARNs
            if "database" in arns:
                if line.startswith("AURORA_CLUSTER_ARN="):
                    if "cluster_arn" in arns["database"]:
                        new_line = f"AURORA_CLUSTER_ARN={arns['database']['cluster_arn']}"
                        if line != new_line:
                            updated_lines.append(new_line)
                            changes_made = True
                            updated = True
                elif line.startswith("AURORA_SECRET_ARN="):
                    if "secret_arn" in arns["database"]:
                        new_line = f"AURORA_SECRET_ARN={arns['database']['secret_arn']}"
                        if line != new_line:
                            updated_lines.append(new_line)
                            changes_made = True
                            updated = True

            # Ingestion ARNs
            if "ingestion" in arns:
                if line.startswith("SQS_QUEUE_URL="):
                    if "queue_url" in arns["ingestion"]:
                        new_line = f"SQS_QUEUE_URL={arns['ingestion']['queue_url']}"
                        if line != new_line:
                            updated_lines.append(new_line)
                            changes_made = True
                            updated = True

            if not updated:
                updated_lines.append(line)

        if not changes_made:
            return False

        if dry_run:
            print(f"  {Colors.BLUE}[DRY RUN]{Colors.END} Would update {env_path}")
            return True

        # Backup and write
        backup_path = self.backup_file(env_path)
        if backup_path:
            print(f"  {Colors.GREEN}✓{Colors.END}  Created backup: {backup_path.name}")

        try:
            env_path.write_text("\n".join(updated_lines) + "\n")
            print(f"  {Colors.GREEN}✓{Colors.END}  Updated {env_path.name}")
            return True
        except PermissionError:
            self.critical_error(
                f"Cannot write to {env_path}. Permission denied.",
                f"Check file permissions: chmod 644 {env_path}"
            )

    def update_tfvars_file(self, file_path: Path, arns: Dict[str, Dict[str, str]], dry_run: bool = False) -> bool:
        """Update terraform.tfvars file with new ARNs"""
        if not file_path.exists():
            print(f"  {Colors.YELLOW}⚠{Colors.END}  {file_path.name} not found, skipping")
            return False

        # Read current content
        try:
            lines = file_path.read_text().splitlines()
        except PermissionError:
            self.critical_error(
                f"Cannot read {file_path}. Permission denied.",
                f"Check file permissions: ls -la {file_path}"
            )

        # Track changes
        updated_lines = []
        changes_made = False

        for line in lines:
            updated = False

            # Database ARNs
            if "database" in arns:
                if line.strip().startswith("aurora_cluster_arn"):
                    if "cluster_arn" in arns["database"]:
                        new_line = f'aurora_cluster_arn = "{arns["database"]["cluster_arn"]}"'
                        if line.strip() != new_line.strip():
                            # Preserve indentation
                            indent = len(line) - len(line.lstrip())
                            updated_lines.append(" " * indent + new_line)
                            changes_made = True
                            updated = True
                elif line.strip().startswith("aurora_secret_arn"):
                    if "secret_arn" in arns["database"]:
                        new_line = f'aurora_secret_arn = "{arns["database"]["secret_arn"]}"'
                        if line.strip() != new_line.strip():
                            # Preserve indentation
                            indent = len(line) - len(line.lstrip())
                            updated_lines.append(" " * indent + new_line)
                            changes_made = True
                            updated = True

            if not updated:
                updated_lines.append(line)

        if not changes_made:
            return False

        if dry_run:
            print(f"  {Colors.BLUE}[DRY RUN]{Colors.END} Would update {file_path}")
            return True

        # Backup and write
        backup_path = self.backup_file(file_path)
        if backup_path:
            print(f"  {Colors.GREEN}✓{Colors.END}  Created backup: {backup_path.name}")

        try:
            file_path.write_text("\n".join(updated_lines) + "\n")
            print(f"  {Colors.GREEN}✓{Colors.END}  Updated {file_path.name}")
            return True
        except PermissionError:
            self.critical_error(
                f"Cannot write to {file_path}. Permission denied.",
                f"Check file permissions: chmod 644 {file_path}"
            )

    def sync(self, dry_run: bool = False, auto: bool = False):
        """Main sync operation"""
        print(f"{Colors.BOLD}🔄 Alex ARN Synchronization{Colors.END}")
        print("=" * 50)

        # Detect ARNs
        arns = self.detect_arn_changes()

        if not arns:
            self.critical_error(
                "No terraform outputs found. Infrastructure not deployed.",
                "Deploy infrastructure first: cd terraform/5_database && terraform apply"
            )

        # Check if database ARNs are present (critical requirement)
        if "database" not in arns:
            self.critical_error(
                "Database module not deployed. Cannot sync critical ARNs.",
                "Deploy database first: cd terraform/5_database && terraform apply"
            )

        # Display detected ARNs
        print(f"\n{Colors.GREEN}✅ Detected ARNs:{Colors.END}")
        for module, module_arns in arns.items():
            print(f"\n  {Colors.BOLD}{module}:{Colors.END}")
            for key, value in module_arns.items():
                # Truncate long ARNs for display
                display_value = value if len(value) <= 70 else value[:67] + "..."
                print(f"    {key}: {display_value}")

        # Confirm if not auto mode and not dry run
        if not auto and not dry_run:
            print(f"\n{Colors.YELLOW}⚠️  Update configuration files with these ARNs?{Colors.END}")
            response = input(f"{Colors.BOLD}Proceed? (y/n):{Colors.END} ").strip().lower()
            if response != 'y':
                print(f"\n{Colors.YELLOW}⚠️  ARN sync cancelled by user.{Colors.END}")
                sys.exit(1)

        # Update files
        print(f"\n{Colors.CYAN}📝 Updating configuration files...{Colors.END}")

        env_updated = self.update_env_file(arns, dry_run)
        tfvars_updated = self.update_tfvars_file(self.config_files["agents_tfvars"], arns, dry_run)

        # Summary
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ARN Sync Complete!{Colors.END}")

        if dry_run:
            print(f"\n{Colors.BLUE}ℹ️  Dry run mode - no files were modified{Colors.END}")
        else:
            print(f"\n{Colors.CYAN}📌 Files updated:{Colors.END}")
            if env_updated:
                print(f"  • {self.config_files['root_env']}")
            if tfvars_updated:
                print(f"  • {self.config_files['agents_tfvars']}")

            print(f"\n{Colors.CYAN}📌 Next steps:{Colors.END}")
            print(f"  1. Review updated files (backups created)")
            print(f"  2. Redeploy agents: cd terraform/6_agents && terraform apply")
            print(f"  3. Test your agents")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync ARNs from terraform outputs to config files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/sync_arns.py              # Interactive mode with confirmation
  uv run scripts/sync_arns.py --auto       # Auto-sync without confirmation
  uv run scripts/sync_arns.py --dry-run    # Preview changes without modifying
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-sync without confirmation prompt"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification (alias for verify_arns.py)"
    )

    args = parser.parse_args()

    # If --verify flag, delegate to verify_arns.py
    if args.verify:
        verify_script = Path(__file__).parent / "verify_arns.py"
        if verify_script.exists():
            import subprocess
            sys.exit(subprocess.run(["uv", "run", str(verify_script)]).returncode)
        else:
            print(f"{Colors.RED}verify_arns.py not found{Colors.END}")
            sys.exit(1)

    # Find project root (directory containing this script's parent)
    project_root = Path(__file__).parent.parent

    # Create manager and run sync
    manager = ARNSyncManager(project_root)
    manager.sync(dry_run=args.dry_run, auto=args.auto)


if __name__ == "__main__":
    main()
