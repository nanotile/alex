#!/usr/bin/env python3
"""
Multi-Cloud Deployment Tool for Alex Project

Unified deployment script that can deploy to AWS, GCP, or both clouds.
Supports module selection, dependency resolution, health checks, and cost estimation.

Usage:
    uv run deploy_multi_cloud.py --cloud aws --modules all
    uv run deploy_multi_cloud.py --cloud gcp --modules database
    uv run deploy_multi_cloud.py --cloud both --modules database,agents --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Color codes for terminal output
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Cloud(Enum):
    AWS = "aws"
    GCP = "gcp"
    BOTH = "both"


@dataclass
class Module:
    """Represents a deployable infrastructure module"""
    name: str
    display_name: str
    cloud: Cloud
    terraform_dir: str
    dependencies: List[str]  # List of module names this depends on
    estimated_monthly_cost: float
    health_check_fn: Optional[callable] = None


# Module definitions
AWS_MODULES = {
    "embeddings": Module(
        name="embeddings",
        display_name="SageMaker Embeddings",
        cloud=Cloud.AWS,
        terraform_dir="terraform/2_sagemaker",
        dependencies=[],
        estimated_monthly_cost=10.0,
    ),
    "ingestion": Module(
        name="ingestion",
        display_name="Document Ingestion",
        cloud=Cloud.AWS,
        terraform_dir="terraform/3_ingestion",
        dependencies=["embeddings"],
        estimated_monthly_cost=1.0,
    ),
    "researcher": Module(
        name="researcher",
        display_name="Research Agent",
        cloud=Cloud.AWS,
        terraform_dir="terraform/4_researcher",
        dependencies=["ingestion"],
        estimated_monthly_cost=51.0,
    ),
    "database": Module(
        name="database",
        display_name="Aurora Database",
        cloud=Cloud.AWS,
        terraform_dir="terraform/5_database",
        dependencies=[],
        estimated_monthly_cost=65.0,
    ),
    "agents": Module(
        name="agents",
        display_name="AI Agents (5 Lambdas)",
        cloud=Cloud.AWS,
        terraform_dir="terraform/6_agents",
        dependencies=["database"],
        estimated_monthly_cost=1.0,
    ),
    "frontend": Module(
        name="frontend",
        display_name="Frontend (S3 + CloudFront)",
        cloud=Cloud.AWS,
        terraform_dir="terraform/7_frontend",
        dependencies=["agents"],
        estimated_monthly_cost=2.0,
    ),
    "monitoring": Module(
        name="monitoring",
        display_name="CloudWatch Monitoring",
        cloud=Cloud.AWS,
        terraform_dir="terraform/8_enterprise",
        dependencies=["frontend"],
        estimated_monthly_cost=6.0,
    ),
}

GCP_MODULES = {
    "foundation": Module(
        name="foundation",
        display_name="GCP Foundation",
        cloud=Cloud.GCP,
        terraform_dir="terraform_GCP/0_foundation",
        dependencies=[],
        estimated_monthly_cost=0.0,
    ),
    "embeddings": Module(
        name="embeddings",
        display_name="Vertex AI Embeddings",
        cloud=Cloud.GCP,
        terraform_dir="terraform_GCP/2_embeddings",
        dependencies=["foundation"],
        estimated_monthly_cost=3.0,
    ),
    "database": Module(
        name="database",
        display_name="Cloud SQL Database",
        cloud=Cloud.GCP,
        terraform_dir="terraform_GCP/5_database",
        dependencies=["foundation"],
        estimated_monthly_cost=30.0,
    ),
    "agents": Module(
        name="agents",
        display_name="Tagger Agent (Cloud Run)",
        cloud=Cloud.GCP,
        terraform_dir="terraform_GCP/6_agents",
        dependencies=["database"],
        estimated_monthly_cost=7.0,
    ),
}


class DeploymentOrchestrator:
    """Orchestrates multi-cloud deployments"""

    def __init__(self, dry_run: bool = False, skip_checks: bool = False):
        self.dry_run = dry_run
        self.skip_checks = skip_checks
        self.project_root = Path(__file__).parent.parent
        self.deployment_start_time = time.time()
        self.deployed_modules: List[Tuple[str, str]] = []  # (cloud, module_name)

    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Color.BOLD}{Color.HEADER}{text}{Color.ENDC}")
        print("=" * len(text))

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Color.OKGREEN}✅ {text}{Color.ENDC}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"{Color.FAIL}❌ {text}{Color.ENDC}")

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Color.WARNING}⚠️  {text}{Color.ENDC}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Color.OKCYAN}ℹ️  {text}{Color.ENDC}")

    def resolve_dependencies(self, modules: List[Module]) -> List[Module]:
        """
        Resolve module dependencies and return deployment order.
        Uses topological sort to ensure dependencies are deployed first.
        Dependencies are cloud-specific to avoid cross-cloud circular dependencies.
        """
        # Build adjacency list with unique keys (cloud + name)
        module_map = {}
        in_degree = {}
        graph = {}

        for m in modules:
            key = f"{m.cloud.value}:{m.name}"
            module_map[key] = m
            in_degree[key] = 0
            graph[key] = []

        # Build dependency graph (only within same cloud)
        for module in modules:
            key = f"{module.cloud.value}:{module.name}"

            for dep in module.dependencies:
                dep_key = f"{module.cloud.value}:{dep}"
                if dep_key in module_map:
                    graph[dep_key].append(key)
                    in_degree[key] += 1

        # Topological sort using Kahn's algorithm
        queue = [key for key, degree in in_degree.items() if degree == 0]
        sorted_order = []

        while queue:
            current = queue.pop(0)
            sorted_order.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != len(modules):
            raise Exception("Circular dependency detected in modules!")

        return [module_map[key] for key in sorted_order]

    def estimate_costs(self, modules: List[Module]) -> Dict[str, float]:
        """Estimate monthly costs by cloud"""
        costs = {"AWS": 0.0, "GCP": 0.0}

        for module in modules:
            cloud_key = "AWS" if module.cloud == Cloud.AWS else "GCP"
            costs[cloud_key] += module.estimated_monthly_cost

        return costs

    def check_prerequisites(self, module: Module) -> bool:
        """Check if module prerequisites are met"""
        terraform_dir = self.project_root / module.terraform_dir

        # Check if directory exists
        if not terraform_dir.exists():
            self.print_error(f"Terraform directory not found: {terraform_dir}")
            return False

        # Check if terraform .tf files exist
        tf_files = list(terraform_dir.glob("*.tf"))
        if not tf_files:
            self.print_warning(f"No .tf files found in {terraform_dir} - skipping")
            return False

        # Check if terraform.tfvars exists
        tfvars_path = terraform_dir / "terraform.tfvars"
        if not tfvars_path.exists():
            self.print_warning(f"terraform.tfvars not found in {terraform_dir}")
            self.print_info(f"Copy terraform.tfvars.example to terraform.tfvars and configure it")
            return False

        return True

    def run_terraform(self, module: Module, command: str) -> Tuple[bool, str]:
        """Run terraform command in module directory"""
        terraform_dir = self.project_root / module.terraform_dir

        if self.dry_run and command == "apply":
            command = "plan"

        try:
            cmd = ["terraform", command]
            if command == "apply":
                cmd.append("-auto-approve")

            print(f"   Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                return False, result.stderr

            return True, result.stdout

        except subprocess.TimeoutExpired:
            return False, "Terraform command timed out after 10 minutes"
        except Exception as e:
            return False, str(e)

    def get_terraform_outputs(self, module: Module) -> Dict:
        """Get terraform outputs as JSON"""
        terraform_dir = self.project_root / module.terraform_dir

        try:
            result = subprocess.run(
                ["terraform", "output", "-json"],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)

        except Exception as e:
            self.print_warning(f"Could not get outputs: {e}")

        return {}

    def health_check_aws_database(self, module: Module) -> bool:
        """Health check for AWS Aurora database"""
        try:
            result = subprocess.run(
                ["aws", "rds", "describe-db-clusters", "--query",
                 "DBClusters[?Status=='available'].DBClusterIdentifier", "--output", "text"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False

    def health_check_gcp_database(self, module: Module) -> bool:
        """Health check for GCP Cloud SQL database"""
        try:
            result = subprocess.run(
                ["gcloud", "sql", "instances", "list", "--format=value(state)"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return "RUNNABLE" in result.stdout
        except Exception:
            return False

    def health_check_gcp_tagger(self, module: Module) -> bool:
        """Health check for GCP Cloud Run tagger service"""
        outputs = self.get_terraform_outputs(module)

        if "service_url" in outputs:
            service_url = outputs["service_url"]["value"]
            health_url = f"{service_url}/health"

            try:
                result = subprocess.run(
                    ["curl", "-s", "-f", health_url],
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0
            except Exception:
                return False

        return False

    def perform_health_check(self, module: Module) -> bool:
        """Perform health check for a deployed module"""
        if self.skip_checks or self.dry_run:
            return True

        print(f"   Health check...", end=" ", flush=True)

        # Map modules to health check functions
        health_checks = {
            ("AWS", "database"): self.health_check_aws_database,
            ("GCP", "database"): self.health_check_gcp_database,
            ("GCP", "agents"): self.health_check_gcp_tagger,
        }

        cloud_key = "AWS" if module.cloud == Cloud.AWS else "GCP"
        check_fn = health_checks.get((cloud_key, module.name))

        if check_fn:
            if check_fn(module):
                print(f"{Color.OKGREEN}✅ Healthy{Color.ENDC}")
                return True
            else:
                print(f"{Color.WARNING}⚠️  Could not verify{Color.ENDC}")
                return True  # Don't fail deployment, just warn
        else:
            print(f"{Color.OKCYAN}(skipped){Color.ENDC}")
            return True

    def deploy_module(self, module: Module, index: int, total: int) -> bool:
        """Deploy a single module"""
        cloud_name = "AWS" if module.cloud == Cloud.AWS else "GCP"

        self.print_info(f"[{index}/{total}] {cloud_name} {module.display_name} ({module.terraform_dir})")

        # Check prerequisites
        if not self.check_prerequisites(module):
            # Check if it's just missing .tf files (already deployed or not applicable)
            terraform_dir = self.project_root / module.terraform_dir
            tf_files = list(terraform_dir.glob("*.tf")) if terraform_dir.exists() else []
            if terraform_dir.exists() and not tf_files:
                self.print_info("   Module already deployed or not applicable - skipping")
                return True  # Don't fail, just skip
            return False

        start_time = time.time()

        # Terraform init
        print(f"   terraform init...", end=" ", flush=True)
        success, output = self.run_terraform(module, "init")
        if not success:
            print(f"{Color.FAIL}failed{Color.ENDC}")
            self.print_error(f"Init failed: {output}")
            return False
        print(f"{Color.OKGREEN}done{Color.ENDC}")

        # Terraform apply/plan
        command = "plan" if self.dry_run else "apply"
        print(f"   terraform {command}...", end=" ", flush=True)
        success, output = self.run_terraform(module, "apply")
        if not success:
            print(f"{Color.FAIL}failed{Color.ENDC}")
            self.print_error(f"Apply failed: {output}")
            return False
        print(f"{Color.OKGREEN}done{Color.ENDC}")

        # Health check
        if not self.perform_health_check(module):
            self.print_warning("Health check failed, but continuing...")

        # Duration
        duration = time.time() - start_time
        print(f"   Duration: {int(duration // 60)}m {int(duration % 60)}s")

        self.deployed_modules.append((cloud_name, module.name))
        return True

    def display_outputs(self, modules: List[Module]):
        """Display deployment outputs and endpoints"""
        self.print_header("Deployment Outputs")

        aws_outputs = {}
        gcp_outputs = {}

        for module in modules:
            outputs = self.get_terraform_outputs(module)
            if module.cloud == Cloud.AWS:
                aws_outputs[module.name] = outputs
            else:
                gcp_outputs[module.name] = outputs

        if aws_outputs:
            print(f"\n{Color.BOLD}AWS Endpoints:{Color.ENDC}")
            for module_name, outputs in aws_outputs.items():
                for key, value_obj in outputs.items():
                    value = value_obj.get("value", "")
                    if value:
                        print(f"  {module_name}.{key}: {value}")

        if gcp_outputs:
            print(f"\n{Color.BOLD}GCP Endpoints:{Color.ENDC}")
            for module_name, outputs in gcp_outputs.items():
                for key, value_obj in outputs.items():
                    value = value_obj.get("value", "")
                    if value:
                        print(f"  {module_name}.{key}: {value}")

    def deploy(self, cloud: Cloud, module_names: List[str]) -> bool:
        """Main deployment orchestration"""
        self.print_header("🚀 Multi-Cloud Deployment Tool for Alex")

        # Gather modules to deploy
        modules_to_deploy = []

        if cloud in [Cloud.AWS, Cloud.BOTH]:
            if "all" in module_names:
                modules_to_deploy.extend(AWS_MODULES.values())
            else:
                for name in module_names:
                    if name in AWS_MODULES:
                        modules_to_deploy.append(AWS_MODULES[name])

        if cloud in [Cloud.GCP, Cloud.BOTH]:
            if "all" in module_names:
                modules_to_deploy.extend(GCP_MODULES.values())
            else:
                for name in module_names:
                    if name in GCP_MODULES:
                        modules_to_deploy.append(GCP_MODULES[name])

        if not modules_to_deploy:
            self.print_error("No modules selected for deployment")
            return False

        # Resolve dependencies
        try:
            ordered_modules = self.resolve_dependencies(modules_to_deploy)
        except Exception as e:
            self.print_error(f"Dependency resolution failed: {e}")
            return False

        # Display plan
        print(f"\n{Color.BOLD}Configuration:{Color.ENDC}")
        print(f"  Cloud: {cloud.value}")
        print(f"  Modules: {', '.join(module_names)}")
        print(f"  Dry Run: {self.dry_run}")

        # Display deployment order
        print(f"\n{Color.BOLD}📋 Deployment Order:{Color.ENDC}")
        for i, module in enumerate(ordered_modules, 1):
            cloud_name = "AWS" if module.cloud == Cloud.AWS else "GCP"
            print(f"  {i}. {cloud_name}: {module.display_name}")

        # Cost estimation
        costs = self.estimate_costs(ordered_modules)
        total_cost = sum(costs.values())

        print(f"\n{Color.BOLD}💰 Estimated Monthly Cost:{Color.ENDC}")
        if costs["AWS"] > 0:
            print(f"  AWS: ${costs['AWS']:.2f}")
        if costs["GCP"] > 0:
            print(f"  GCP: ${costs['GCP']:.2f}")
        print(f"  {Color.BOLD}Total: ${total_cost:.2f}/month{Color.ENDC}")

        # Confirmation
        if not self.dry_run:
            response = input(f"\n{Color.WARNING}Continue? [y/N]: {Color.ENDC}")
            if response.lower() != 'y':
                print("Deployment cancelled.")
                return False

        # Deploy modules
        print()
        success = True
        for i, module in enumerate(ordered_modules, 1):
            if not self.deploy_module(module, i, len(ordered_modules)):
                self.print_error(f"Deployment failed at module: {module.display_name}")
                success = False
                break
            print()  # Blank line between modules

        # Summary
        total_duration = time.time() - self.deployment_start_time

        if success:
            self.print_success(f"🎉 Deployment Complete! (Total: {int(total_duration // 60)}m {int(total_duration % 60)}s)")

            if not self.dry_run:
                self.display_outputs(ordered_modules)

                print(f"\n{Color.BOLD}Next Steps:{Color.ENDC}")
                print("  - Update frontend/.env.production.local with API_URL")
                print("  - Test endpoints with curl or browser")
                print("  - Monitor costs in AWS/GCP consoles")
        else:
            self.print_error("Deployment failed. Check errors above.")

        return success


def main():
    parser = argparse.ArgumentParser(
        description="Multi-cloud deployment tool for Alex project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Deploy everything to AWS:
    uv run deploy_multi_cloud.py --cloud aws --modules all

  Deploy database to GCP:
    uv run deploy_multi_cloud.py --cloud gcp --modules database

  Deploy to both clouds (database + agents):
    uv run deploy_multi_cloud.py --cloud both --modules database,agents

  Dry run (preview without executing):
    uv run deploy_multi_cloud.py --cloud both --modules all --dry-run
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
        help="Comma-separated list of modules to deploy (e.g., 'database,agents' or 'all')"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deployment without executing (runs terraform plan instead of apply)"
    )

    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip health checks after deployment (faster)"
    )

    args = parser.parse_args()

    # Parse modules
    module_names = [m.strip() for m in args.modules.split(",")]

    # Create orchestrator
    orchestrator = DeploymentOrchestrator(
        dry_run=args.dry_run,
        skip_checks=args.skip_checks
    )

    # Run deployment
    try:
        success = orchestrator.deploy(Cloud(args.cloud), module_names)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Color.WARNING}Deployment cancelled by user{Color.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Color.FAIL}Unexpected error: {e}{Color.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
