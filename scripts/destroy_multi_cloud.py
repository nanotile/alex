#!/usr/bin/env python3
"""
Multi-Cloud Destroy Tool for Alex Project

Safely destroy infrastructure deployed to AWS, GCP, or both clouds.
Destroys in reverse dependency order to avoid errors.

Usage:
    uv run destroy_multi_cloud.py --cloud aws --modules all
    uv run destroy_multi_cloud.py --cloud gcp --modules database
    uv run destroy_multi_cloud.py --cloud both --modules database,agents --dry-run
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

# Reuse Color class
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# Import module definitions from deploy script
try:
    from deploy_multi_cloud import AWS_MODULES, GCP_MODULES, Cloud, Module, DeploymentOrchestrator
except ImportError:
    print(f"{Color.FAIL}Error: Could not import from deploy_multi_cloud.py{Color.ENDC}")
    print("Make sure deploy_multi_cloud.py is in the same directory.")
    sys.exit(1)


class DestroyOrchestrator(DeploymentOrchestrator):
    """Orchestrates multi-cloud infrastructure destruction"""

    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run=dry_run, skip_checks=True)

    def destroy_module(self, module: Module, index: int, total: int) -> bool:
        """Destroy a single module"""
        cloud_name = "AWS" if module.cloud == Cloud.AWS else "GCP"

        self.print_info(f"[{index}/{total}] {cloud_name} {module.display_name} ({module.terraform_dir})")

        terraform_dir = self.project_root / module.terraform_dir

        if not terraform_dir.exists():
            self.print_warning(f"Directory not found: {terraform_dir}")
            return True  # Not an error, just skip

        # Check if state exists
        state_file = terraform_dir / "terraform.tfstate"
        if not state_file.exists():
            self.print_info("   No state file found (nothing to destroy)")
            return True

        start_time = time.time()

        # Terraform init (in case providers changed)
        print(f"   terraform init...", end=" ", flush=True)
        try:
            result = subprocess.run(
                ["terraform", "init"],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                print(f"{Color.FAIL}failed{Color.ENDC}")
                self.print_error(f"Init failed: {result.stderr}")
                return False
            print(f"{Color.OKGREEN}done{Color.ENDC}")
        except Exception as e:
            print(f"{Color.FAIL}failed{Color.ENDC}")
            self.print_error(str(e))
            return False

        # Terraform destroy
        command = "plan -destroy" if self.dry_run else "destroy"
        print(f"   terraform {command}...", end=" ", flush=True)

        try:
            cmd = ["terraform", "destroy"] if not self.dry_run else ["terraform", "plan", "-destroy"]
            if not self.dry_run:
                cmd.append("-auto-approve")

            result = subprocess.run(
                cmd,
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                print(f"{Color.FAIL}failed{Color.ENDC}")
                self.print_error(f"Destroy failed: {result.stderr}")
                return False

            print(f"{Color.OKGREEN}done{Color.ENDC}")

        except subprocess.TimeoutExpired:
            print(f"{Color.FAIL}timeout{Color.ENDC}")
            return False
        except Exception as e:
            print(f"{Color.FAIL}failed{Color.ENDC}")
            self.print_error(str(e))
            return False

        # Duration
        duration = time.time() - start_time
        print(f"   Duration: {int(duration // 60)}m {int(duration % 60)}s")

        return True

    def destroy(self, cloud: Cloud, module_names: List[str]) -> bool:
        """Main destruction orchestration"""
        self.print_header("🗑️  Multi-Cloud Destroy Tool for Alex")

        # Gather modules to destroy
        modules_to_destroy = []

        if cloud in [Cloud.AWS, Cloud.BOTH]:
            if "all" in module_names:
                modules_to_destroy.extend(AWS_MODULES.values())
            else:
                for name in module_names:
                    if name in AWS_MODULES:
                        modules_to_destroy.append(AWS_MODULES[name])

        if cloud in [Cloud.GCP, Cloud.BOTH]:
            if "all" in module_names:
                modules_to_destroy.extend(GCP_MODULES.values())
            else:
                for name in module_names:
                    if name in GCP_MODULES:
                        modules_to_destroy.append(GCP_MODULES[name])

        if not modules_to_destroy:
            self.print_error("No modules selected for destruction")
            return False

        # Reverse dependency order (destroy dependents first)
        try:
            ordered_modules = self.resolve_dependencies(modules_to_destroy)
            ordered_modules.reverse()  # Destroy in reverse order
        except Exception as e:
            self.print_error(f"Dependency resolution failed: {e}")
            return False

        # Display plan
        print(f"\n{Color.BOLD}Configuration:{Color.ENDC}")
        print(f"  Cloud: {cloud.value}")
        print(f"  Modules: {', '.join(module_names)}")
        print(f"  Dry Run: {self.dry_run}")

        # Display destruction order
        print(f"\n{Color.BOLD}📋 Destruction Order:{Color.ENDC}")
        for i, module in enumerate(ordered_modules, 1):
            cloud_name = "AWS" if module.cloud == Cloud.AWS else "GCP"
            print(f"  {i}. {cloud_name}: {module.display_name}")

        # Cost savings
        costs = self.estimate_costs(ordered_modules)
        total_savings = sum(costs.values())

        print(f"\n{Color.BOLD}💰 Monthly Cost Savings:{Color.ENDC}")
        if costs["AWS"] > 0:
            print(f"  AWS: ${costs['AWS']:.2f}")
        if costs["GCP"] > 0:
            print(f"  GCP: ${costs['GCP']:.2f}")
        print(f"  {Color.BOLD}Total: ${total_savings:.2f}/month{Color.ENDC}")

        # Confirmation with extra warning
        if not self.dry_run:
            print(f"\n{Color.FAIL}{Color.BOLD}⚠️  WARNING: This will PERMANENTLY DELETE the selected infrastructure!{Color.ENDC}")
            response = input(f"{Color.WARNING}Type 'destroy' to confirm: {Color.ENDC}")
            if response.lower() != 'destroy':
                print("Destruction cancelled.")
                return False

        # Destroy modules
        print()
        success = True
        for i, module in enumerate(ordered_modules, 1):
            if not self.destroy_module(module, i, len(ordered_modules)):
                self.print_error(f"Destruction failed at module: {module.display_name}")
                success = False
                break
            print()  # Blank line between modules

        # Summary
        total_duration = time.time() - self.deployment_start_time

        if success:
            self.print_success(f"✅ Destruction Complete! (Total: {int(total_duration // 60)}m {int(total_duration % 60)}s)")
            if not self.dry_run:
                print(f"\n{Color.BOLD}Resources Destroyed:{Color.ENDC}")
                for module in ordered_modules:
                    cloud_name = "AWS" if module.cloud == Cloud.AWS else "GCP"
                    print(f"  - {cloud_name}: {module.display_name}")
                print(f"\n{Color.OKGREEN}💰 You will save ~${total_savings:.2f}/month{Color.ENDC}")
        else:
            self.print_error("Destruction failed. Check errors above.")
            self.print_warning("Some resources may still exist. Check AWS/GCP consoles.")

        return success


def main():
    parser = argparse.ArgumentParser(
        description="Multi-cloud destroy tool for Alex project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Destroy everything on AWS:
    uv run destroy_multi_cloud.py --cloud aws --modules all

  Destroy database on GCP:
    uv run destroy_multi_cloud.py --cloud gcp --modules database

  Destroy database + agents on both clouds:
    uv run destroy_multi_cloud.py --cloud both --modules database,agents

  Dry run (preview without executing):
    uv run destroy_multi_cloud.py --cloud both --modules all --dry-run

Cost-saving recommendations:
  - Destroy 'researcher' to save $51/month (AWS App Runner)
  - Destroy 'database' to save $65/month (AWS Aurora) or $30/month (GCP Cloud SQL)
  - Use --dry-run first to see what will be destroyed
        """
    )

    parser.add_argument(
        "--cloud",
        type=str,
        choices=["aws", "gcp", "both"],
        required=True,
        help="Target cloud: aws, gcp, or both"
    )

    parser.add_argument(
        "--modules",
        type=str,
        required=True,
        help="Comma-separated list of modules to destroy (e.g., 'database,agents' or 'all')"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview destruction without executing (runs terraform plan -destroy)"
    )

    args = parser.parse_args()

    # Parse modules
    module_names = [m.strip() for m in args.modules.split(",")]

    # Create orchestrator
    orchestrator = DestroyOrchestrator(dry_run=args.dry_run)

    # Run destruction
    try:
        success = orchestrator.destroy(Cloud(args.cloud), module_names)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Color.WARNING}Destruction cancelled by user{Color.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Color.FAIL}Unexpected error: {e}{Color.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
