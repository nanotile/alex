"""
ARN Verification Script for Alex Project

Checks for inconsistencies between terraform outputs and configuration files.
Helps diagnose authorization errors due to stale ARNs.

Usage:
    uv run scripts/verify_arns.py

Exit Codes:
    0: Success, all ARNs are in sync
    2: Verification failed, ARNs are out of sync
    1: Critical error (terraform not deployed, etc.)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


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


class ARNVerifier:
    """Verifies ARN consistency between terraform and configuration files"""

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

    def read_terraform_outputs(self, tf_dir: Path) -> Optional[Dict]:
        """Read terraform outputs as JSON"""
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
                return None

            return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return None

    def extract_arn_values(self, outputs: Dict) -> Dict[str, str]:
        """Extract ARN values from terraform output JSON"""
        arns = {}
        for key, value in outputs.items():
            if isinstance(value, dict) and "value" in value:
                arns[key] = value["value"]
        return arns

    def read_env_arns(self) -> Dict[str, str]:
        """Read ARNs from .env file"""
        env_path = self.config_files["root_env"]
        arns = {}

        if not env_path.exists():
            return arns

        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("AURORA_CLUSTER_ARN="):
                    arns["cluster_arn"] = line.split("=", 1)[1]
                elif line.startswith("AURORA_SECRET_ARN="):
                    arns["secret_arn"] = line.split("=", 1)[1]
                elif line.startswith("SQS_QUEUE_URL="):
                    arns["queue_url"] = line.split("=", 1)[1]
        except Exception:
            pass

        return arns

    def read_tfvars_arns(self, tfvars_path: Path) -> Dict[str, str]:
        """Read ARNs from terraform.tfvars file"""
        arns = {}

        if not tfvars_path.exists():
            return arns

        try:
            for line in tfvars_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("aurora_cluster_arn"):
                    # Extract value between quotes
                    value = line.split("=", 1)[1].strip().strip('"')
                    arns["cluster_arn"] = value
                elif line.startswith("aurora_secret_arn"):
                    value = line.split("=", 1)[1].strip().strip('"')
                    arns["secret_arn"] = value
        except Exception:
            pass

        return arns

    def highlight_difference(self, str1: str, str2: str) -> Tuple[str, str]:
        """Highlight the difference between two strings"""
        # Find the first position where they differ
        min_len = min(len(str1), len(str2))
        diff_pos = min_len

        for i in range(min_len):
            if str1[i] != str2[i]:
                diff_pos = i
                break

        # If lengths are different, mark from the end of the shorter one
        if len(str1) != len(str2) and diff_pos == min_len:
            diff_pos = min_len

        # Highlight the different part
        if diff_pos < len(str1):
            highlighted1 = str1[:diff_pos] + f"{Colors.RED}{Colors.BOLD}{str1[diff_pos:]}{Colors.END}"
        else:
            highlighted1 = str1

        if diff_pos < len(str2):
            highlighted2 = str2[:diff_pos] + f"{Colors.RED}{Colors.BOLD}{str2[diff_pos:]}{Colors.END}"
        else:
            highlighted2 = str2

        return highlighted1, highlighted2

    def verify(self) -> bool:
        """Verify ARN consistency"""
        print(f"{Colors.BOLD}🔍 Alex ARN Verification{Colors.END}")
        print("=" * 50)

        # Read terraform outputs
        print(f"\n{Colors.CYAN}📋 Reading terraform outputs...{Colors.END}")
        tf_arns = {}

        for name, tf_dir in self.terraform_dirs.items():
            if not tf_dir.exists():
                continue

            outputs = self.read_terraform_outputs(tf_dir)
            if outputs:
                arns = self.extract_arn_values(outputs)
                if arns:
                    tf_arns[name] = arns
                    print(f"  {Colors.GREEN}✓{Colors.END}  {name}: {len(arns)} ARN(s)")

        if not tf_arns:
            print(f"\n{Colors.RED}❌ No terraform outputs found{Colors.END}")
            print(f"{Colors.YELLOW}Deploy infrastructure first:{Colors.END}")
            print(f"  cd terraform/5_database && terraform apply")
            return False

        # Read config files
        print(f"\n{Colors.CYAN}📋 Reading configuration files...{Colors.END}")
        env_arns = self.read_env_arns()
        tfvars_arns = self.read_tfvars_arns(self.config_files["agents_tfvars"])

        if env_arns:
            print(f"  {Colors.GREEN}✓{Colors.END}  .env: {len(env_arns)} ARN(s)")
        if tfvars_arns:
            print(f"  {Colors.GREEN}✓{Colors.END}  terraform.tfvars: {len(tfvars_arns)} ARN(s)")

        # Compare
        mismatches = []

        if "database" in tf_arns:
            for key in ["cluster_arn", "secret_arn"]:
                tf_value = tf_arns["database"].get(key)
                env_value = env_arns.get(key)
                tfvars_value = tfvars_arns.get(key)

                # Check .env mismatch
                if tf_value and env_value and tf_value != env_value:
                    mismatches.append({
                        "arn_key": key,
                        "file": ".env",
                        "terraform": tf_value,
                        "config": env_value
                    })

                # Check terraform.tfvars mismatch
                if tf_value and tfvars_value and tf_value != tfvars_value:
                    mismatches.append({
                        "arn_key": key,
                        "file": "terraform.tfvars",
                        "terraform": tf_value,
                        "config": tfvars_value
                    })

        # Report results
        print(f"\n{Colors.CYAN}📊 Verification Results{Colors.END}")
        print("=" * 50)

        if mismatches:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ARN Mismatches Detected!{Colors.END}\n")

            for mismatch in mismatches:
                print(f"  {Colors.BOLD}{mismatch['arn_key']}{Colors.END} in {mismatch['file']}:")

                # Highlight the difference
                tf_highlighted, config_highlighted = self.highlight_difference(
                    mismatch['terraform'],
                    mismatch['config']
                )

                print(f"    Terraform: {tf_highlighted}")
                print(f"    Config:    {config_highlighted}")
                print()

            print(f"{Colors.RED}{Colors.BOLD}❌ VERIFICATION FAILED{Colors.END}")
            print(f"\n{Colors.YELLOW}🔧 Fix with:{Colors.END}")
            print(f"  uv run scripts/sync_arns.py")
            print(f"\n{Colors.YELLOW}Or manually update:{Colors.END}")
            for mismatch in mismatches:
                print(f"  • {mismatch['file']}: {mismatch['arn_key']}")

            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All ARNs are in sync!{Colors.END}")
            print(f"\n{Colors.CYAN}ℹ️  Terraform outputs match configuration files{Colors.END}")
            return True


def main():
    # Find project root
    project_root = Path(__file__).parent.parent

    # Create verifier and run
    verifier = ARNVerifier(project_root)
    success = verifier.verify()

    # Exit with appropriate code
    sys.exit(0 if success else 2)


if __name__ == "__main__":
    main()
