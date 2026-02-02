#!/usr/bin/env python3
"""
AWS Deployment Status Tool for Alex Project

Comprehensive status checker that shows what's deployed, what's missing,
resource health, and recommendations.

Usage:
    uv run deployment_status.py                    # Full status report
    uv run deployment_status.py --summary          # Quick summary only
    uv run deployment_status.py --json             # JSON output for automation
    uv run deployment_status.py --module 5_database  # Check specific module
    uv run deployment_status.py --health           # Include health checks
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


@dataclass
class ModuleStatus:
    """Status information for a terraform module"""
    module_id: str
    name: str
    description: str
    is_deployed: bool
    resource_count: int
    monthly_cost: float
    health_status: Optional[str] = None
    outputs: Optional[Dict] = None
    last_modified: Optional[str] = None
    terraform_initialized: bool = False
    tfvars_exists: bool = False


# Module definitions (matching minimize_costs.py)
MODULE_DEFINITIONS = {
    "2_sagemaker": {
        "name": "SageMaker Serverless",
        "description": "Embedding endpoint (pay-per-use)",
        "monthly_cost": 10,
        "priority": 3,
        "category": "AI/ML",
    },
    "3_ingestion": {
        "name": "Ingestion Pipeline",
        "description": "Lambda + API Gateway (pay-per-use)",
        "monthly_cost": 1,
        "priority": 7,
        "category": "Data",
    },
    "4_researcher": {
        "name": "App Runner Service",
        "description": "Research agent container (1vCPU, 2GB)",
        "monthly_cost": 51,
        "priority": 2,
        "category": "AI Agents",
    },
    "5_database": {
        "name": "Aurora Serverless v2",
        "description": "PostgreSQL database (0.5-1 ACU)",
        "monthly_cost": 65,
        "priority": 1,
        "category": "Database",
    },
    "6_agents": {
        "name": "Lambda Agents",
        "description": "5 Lambda functions + SQS (pay-per-use)",
        "monthly_cost": 1,
        "priority": 6,
        "category": "AI Agents",
    },
    "7_frontend": {
        "name": "Frontend Infrastructure",
        "description": "CloudFront + S3 + API Gateway (pay-per-use)",
        "monthly_cost": 2,
        "priority": 5,
        "category": "Frontend",
    },
    "8_enterprise": {
        "name": "CloudWatch Dashboards",
        "description": "Monitoring dashboards (2 dashboards)",
        "monthly_cost": 6,
        "priority": 4,
        "category": "Monitoring",
    },
}


class DeploymentStatusChecker:
    """Check AWS deployment status"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.terraform_dir = self.project_root / "terraform"

    def get_module_terraform_dir(self, module_id: str) -> Path:
        """Get terraform directory for a module"""
        return self.terraform_dir / module_id

    def check_terraform_state(self, module_id: str) -> Tuple[bool, int, Optional[str]]:
        """
        Check if a terraform module is deployed.
        Returns: (is_deployed, resource_count, last_modified)
        """
        state_file = self.get_module_terraform_dir(module_id) / "terraform.tfstate"

        if not state_file.exists():
            return False, 0, None

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                resources = state.get("resources", [])

                # Get last modified time
                last_modified = datetime.fromtimestamp(state_file.stat().st_mtime)
                last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M:%S")

                return len(resources) > 0, len(resources), last_modified_str
        except (json.JSONDecodeError, KeyError, OSError):
            return False, 0, None

    def check_terraform_initialized(self, module_id: str) -> bool:
        """Check if terraform is initialized for a module"""
        terraform_lock = self.get_module_terraform_dir(module_id) / ".terraform"
        return terraform_lock.exists()

    def check_tfvars_exists(self, module_id: str) -> bool:
        """Check if terraform.tfvars exists for a module"""
        tfvars_file = self.get_module_terraform_dir(module_id) / "terraform.tfvars"
        return tfvars_file.exists()

    def get_terraform_outputs(self, module_id: str) -> Optional[Dict]:
        """Get terraform outputs for a deployed module"""
        terraform_dir = self.get_module_terraform_dir(module_id)

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
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass

        return None

    def check_aws_resource_health(self, module_id: str) -> Optional[str]:
        """Check health of AWS resources for specific modules"""
        try:
            if module_id == "5_database":
                # Check Aurora cluster status
                result = subprocess.run(
                    ["aws", "rds", "describe-db-clusters",
                     "--query", "DBClusters[?contains(DBClusterIdentifier, 'alex')].{Id:DBClusterIdentifier,Status:Status}",
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    clusters = json.loads(result.stdout)
                    if clusters:
                        statuses = [c['Status'] for c in clusters]
                        if all(s == 'available' for s in statuses):
                            return "✅ Healthy (available)"
                        else:
                            return f"⚠️  Status: {', '.join(statuses)}"
                    else:
                        return "❌ No clusters found"

            elif module_id == "4_researcher":
                # Check App Runner service status
                result = subprocess.run(
                    ["aws", "apprunner", "list-services",
                     "--query", "ServiceSummaryList[?contains(ServiceName, 'alex')].{Name:ServiceName,Status:Status}",
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    services = json.loads(result.stdout)
                    if services:
                        statuses = [s['Status'] for s in services]
                        if all(s == 'RUNNING' for s in statuses):
                            return "✅ Healthy (running)"
                        else:
                            return f"⚠️  Status: {', '.join(statuses)}"
                    else:
                        return "❌ No services found"

            elif module_id == "6_agents":
                # Check Lambda functions
                result = subprocess.run(
                    ["aws", "lambda", "list-functions",
                     "--query", "Functions[?starts_with(FunctionName, 'alex')].FunctionName",
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    functions = json.loads(result.stdout)
                    if len(functions) >= 5:
                        return f"✅ Healthy ({len(functions)} functions)"
                    elif len(functions) > 0:
                        return f"⚠️  Only {len(functions)} functions (expected 5)"
                    else:
                        return "❌ No functions found"

            elif module_id == "2_sagemaker":
                # Check SageMaker endpoints
                result = subprocess.run(
                    ["aws", "sagemaker", "list-endpoints",
                     "--query", "Endpoints[?contains(EndpointName, 'alex')].{Name:EndpointName,Status:EndpointStatus}",
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    endpoints = json.loads(result.stdout)
                    if endpoints:
                        statuses = [e['Status'] for e in endpoints]
                        if all(s == 'InService' for s in statuses):
                            return "✅ Healthy (InService)"
                        else:
                            return f"⚠️  Status: {', '.join(statuses)}"
                    else:
                        return "❌ No endpoints found"

            elif module_id == "7_frontend":
                # Check CloudFront distributions
                result = subprocess.run(
                    ["aws", "cloudfront", "list-distributions",
                     "--query", "DistributionList.Items[?Comment=='Alex Frontend'].{Id:Id,Status:Status}",
                     "--output", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    distributions = json.loads(result.stdout)
                    if distributions:
                        statuses = [d['Status'] for d in distributions]
                        if all(s == 'Deployed' for s in statuses):
                            return "✅ Healthy (deployed)"
                        else:
                            return f"⚠️  Status: {', '.join(statuses)}"
                    else:
                        return "❌ No distributions found"

        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            return "⚠️  Health check failed"

        return None

    def get_module_status(self, module_id: str, include_health: bool = False) -> ModuleStatus:
        """Get complete status for a single module"""
        module_def = MODULE_DEFINITIONS.get(module_id, {})

        is_deployed, resource_count, last_modified = self.check_terraform_state(module_id)
        terraform_initialized = self.check_terraform_initialized(module_id)
        tfvars_exists = self.check_tfvars_exists(module_id)

        outputs = None
        health_status = None

        if is_deployed:
            outputs = self.get_terraform_outputs(module_id)

            if include_health:
                health_status = self.check_aws_resource_health(module_id)

        return ModuleStatus(
            module_id=module_id,
            name=module_def.get("name", module_id),
            description=module_def.get("description", "N/A"),
            is_deployed=is_deployed,
            resource_count=resource_count,
            monthly_cost=module_def.get("monthly_cost", 0),
            health_status=health_status,
            outputs=outputs,
            last_modified=last_modified,
            terraform_initialized=terraform_initialized,
            tfvars_exists=tfvars_exists,
        )

    def get_all_module_statuses(self, include_health: bool = False) -> List[ModuleStatus]:
        """Get status for all modules"""
        statuses = []

        for module_id in MODULE_DEFINITIONS.keys():
            status = self.get_module_status(module_id, include_health)
            statuses.append(status)

        # Sort by priority (high-cost resources first)
        priority_map = {m_id: info['priority'] for m_id, info in MODULE_DEFINITIONS.items()}
        statuses.sort(key=lambda s: priority_map.get(s.module_id, 999))

        return statuses

    def calculate_totals(self, statuses: List[ModuleStatus]) -> Dict:
        """Calculate total resources and costs with clear terminology"""
        deployed = [s for s in statuses if s.is_deployed]
        not_deployed = [s for s in statuses if not s.is_deployed]

        total_resources = sum(s.resource_count for s in deployed)
        current_monthly_cost = sum(s.monthly_cost for s in deployed)
        avoided_monthly_cost = sum(s.monthly_cost for s in not_deployed)
        potential_max_cost = sum(s.monthly_cost for s in statuses)

        return {
            "total_modules": len(statuses),
            "deployed_count": len(deployed),
            "not_deployed_count": len(not_deployed),
            "total_resources": total_resources,
            "current_monthly_cost": current_monthly_cost,
            "current_daily_cost": round(current_monthly_cost / 30, 2),
            "avoided_monthly_cost": avoided_monthly_cost,  # Resources not deployed
            "potential_max_cost": potential_max_cost,  # If all modules deployed
            "actual_savings_pct": round((avoided_monthly_cost / potential_max_cost * 100), 1) if potential_max_cost > 0 else 0,
            # Legacy keys for backward compatibility
            "monthly_cost": current_monthly_cost,
            "daily_cost": round(current_monthly_cost / 30, 2),
            "potential_savings": avoided_monthly_cost,
        }


def print_status_report(statuses: List[ModuleStatus], totals: Dict, include_health: bool = False):
    """Print formatted status report"""
    print(f"\n{Color.BOLD}{Color.HEADER}=" * 70)
    print("📊 AWS DEPLOYMENT STATUS - ALEX PROJECT")
    print(f"{'=' * 70}{Color.ENDC}\n")

    print(f"{Color.BOLD}Report Generated:{Color.ENDC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Color.BOLD}AWS Region:{Color.ENDC} ", end="")

    try:
        result = subprocess.run(
            ["aws", "configure", "get", "region"],
            capture_output=True,
            text=True,
            timeout=5
        )
        region = result.stdout.strip() or "Unknown"
        print(region)
    except:
        print("Unknown")

    # Overall Status
    print(f"\n{Color.BOLD}📦 Overall Status:{Color.ENDC}")
    print(f"   Total Modules: {totals['total_modules']}")
    print(f"   Deployed: {Color.OKGREEN}{totals['deployed_count']}{Color.ENDC}")
    print(f"   Not Deployed: {Color.WARNING}{totals['not_deployed_count']}{Color.ENDC}")
    print(f"   Total Resources: {totals['total_resources']}")

    # Cost Information
    print(f"\n{Color.BOLD}💰 Cost Information:{Color.ENDC}")
    print(f"   Current Monthly Cost: ${totals['current_monthly_cost']:.2f}/month")
    print(f"   Current Daily Cost: ${totals['current_daily_cost']:.2f}/day")
    print(f"   Max Possible Cost: ${totals['potential_max_cost']:.2f}/month (if all modules deployed)")

    if totals['not_deployed_count'] > 0:
        print(f"   {Color.OKGREEN}Currently Avoiding: ${totals['avoided_monthly_cost']:.2f}/month (resources not deployed){Color.ENDC}")
        print(f"   {Color.OKGREEN}Savings: {totals['actual_savings_pct']:.1f}% of maximum cost{Color.ENDC}")

    # Deployed Modules
    deployed = [s for s in statuses if s.is_deployed]
    if deployed:
        print(f"\n{Color.BOLD}✅ Deployed Modules ({len(deployed)}):{Color.ENDC}")

        for status in deployed:
            cost_str = f"${status.monthly_cost}/mo" if status.monthly_cost > 0 else "pay-per-use"

            print(f"\n   {Color.OKGREEN}●{Color.ENDC} {Color.BOLD}{status.name}{Color.ENDC} ({status.module_id})")
            print(f"      Description: {status.description}")
            print(f"      Resources: {status.resource_count}")
            print(f"      Cost: {cost_str}")

            if status.last_modified:
                print(f"      Last Modified: {status.last_modified}")

            if include_health and status.health_status:
                print(f"      Health: {status.health_status}")

            # Show key outputs
            if status.outputs:
                important_outputs = {}
                for key, value_obj in status.outputs.items():
                    value = value_obj.get("value", "")
                    # Filter to important outputs only
                    if key in ["cluster_arn", "service_url", "api_url", "distribution_domain",
                               "endpoint_name", "api_gateway_url", "cloudfront_url"]:
                        important_outputs[key] = value

                if important_outputs:
                    print(f"      Key Outputs:")
                    for key, value in important_outputs.items():
                        # Truncate long values
                        display_value = str(value)[:80] + "..." if len(str(value)) > 80 else str(value)
                        print(f"         {key}: {display_value}")

    # Not Deployed Modules
    not_deployed = [s for s in statuses if not s.is_deployed]
    if not_deployed:
        print(f"\n{Color.BOLD}❌ Not Deployed Modules ({len(not_deployed)}):{Color.ENDC}")

        for status in not_deployed:
            cost_str = f"${status.monthly_cost}/mo" if status.monthly_cost > 0 else "pay-per-use"

            print(f"\n   {Color.WARNING}○{Color.ENDC} {Color.BOLD}{status.name}{Color.ENDC} ({status.module_id})")
            print(f"      Description: {status.description}")
            print(f"      Would Cost: {cost_str}")

            # Configuration status
            config_issues = []
            if not status.terraform_initialized:
                config_issues.append("terraform not initialized")
            if not status.tfvars_exists:
                config_issues.append("terraform.tfvars missing")

            if config_issues:
                print(f"      {Color.WARNING}⚠️  Issues: {', '.join(config_issues)}{Color.ENDC}")
            else:
                print(f"      {Color.OKGREEN}✓{Color.ENDC} Configuration ready")

    # Recommendations
    print(f"\n{Color.BOLD}💡 Recommendations:{Color.ENDC}")

    if totals['monthly_cost'] > 100:
        print(f"   {Color.WARNING}⚠️  High monthly costs (${totals['monthly_cost']:.2f}){Color.ENDC}")
        print(f"      Consider: uv run scripts/AWS_START_STOP/minimize_costs.py --mode shutdown")

    if totals['deployed_count'] == 0:
        print(f"   {Color.OKGREEN}✅ No resources deployed - minimal costs!{Color.ENDC}")
        print(f"      To deploy: uv run scripts/AWS_START_STOP/restart_infrastructure.py --preset daily")

    # Check for specific missing components
    database_deployed = any(s.is_deployed and s.module_id == "5_database" for s in statuses)
    agents_deployed = any(s.is_deployed and s.module_id == "6_agents" for s in statuses)

    if database_deployed and not agents_deployed:
        print(f"   {Color.WARNING}⚠️  Database deployed but agents are not{Color.ENDC}")
        print(f"      Consider: uv run scripts/AWS_START_STOP/restart_infrastructure.py --modules 6_agents")

    if agents_deployed and not database_deployed:
        print(f"   {Color.FAIL}⚠️  Agents deployed but database is NOT - agents won't work!{Color.ENDC}")
        print(f"      Deploy database: uv run scripts/AWS_START_STOP/restart_infrastructure.py --modules 5_database")

    # Configuration warnings
    not_configured = [s for s in not_deployed if not s.tfvars_exists]
    if not_configured:
        print(f"   {Color.WARNING}⚠️  {len(not_configured)} modules missing terraform.tfvars{Color.ENDC}")
        for status in not_configured:
            print(f"      - {status.module_id}: Copy terraform.tfvars.example to terraform.tfvars")

    print(f"\n{Color.BOLD}{'=' * 70}{Color.ENDC}\n")


def print_summary(statuses: List[ModuleStatus], totals: Dict):
    """Print quick summary"""
    print(f"\n{Color.BOLD}📊 Quick Summary{Color.ENDC}")
    print(f"{'=' * 40}")
    print(f"Deployed: {Color.OKGREEN}{totals['deployed_count']}/{totals['total_modules']}{Color.ENDC}")
    print(f"Resources: {totals['total_resources']}")
    print(f"Monthly Cost: ${totals['monthly_cost']:.2f}")
    print(f"Daily Cost: ${totals['daily_cost']:.2f}")

    deployed = [s for s in statuses if s.is_deployed]
    if deployed:
        print(f"\nDeployed: {', '.join(s.module_id for s in deployed)}")
    else:
        print(f"\n{Color.OKGREEN}No resources deployed{Color.ENDC}")

    print()


def output_json(statuses: List[ModuleStatus], totals: Dict):
    """Output status as JSON"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "totals": totals,
        "modules": [
            {
                "module_id": s.module_id,
                "name": s.name,
                "description": s.description,
                "is_deployed": s.is_deployed,
                "resource_count": s.resource_count,
                "monthly_cost": s.monthly_cost,
                "health_status": s.health_status,
                "last_modified": s.last_modified,
                "terraform_initialized": s.terraform_initialized,
                "tfvars_exists": s.tfvars_exists,
                "outputs": s.outputs,
            }
            for s in statuses
        ]
    }

    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Check AWS deployment status for Alex project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full status report
  uv run deployment_status.py

  # Quick summary
  uv run deployment_status.py --summary

  # Include health checks (slower)
  uv run deployment_status.py --health

  # Check specific module
  uv run deployment_status.py --module 5_database

  # JSON output for automation
  uv run deployment_status.py --json
        """
    )

    parser.add_argument("--summary", action="store_true", help="Show quick summary only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--module", type=str, help="Check specific module only")
    parser.add_argument("--health", action="store_true", help="Include AWS health checks (slower)")

    args = parser.parse_args()

    # Create checker
    checker = DeploymentStatusChecker()

    try:
        # Get statuses
        if args.module:
            if args.module not in MODULE_DEFINITIONS:
                print(f"{Color.FAIL}Error: Unknown module '{args.module}'{Color.ENDC}")
                print(f"Available modules: {', '.join(MODULE_DEFINITIONS.keys())}")
                sys.exit(1)

            statuses = [checker.get_module_status(args.module, args.health)]
        else:
            statuses = checker.get_all_module_statuses(args.health)

        # Calculate totals
        totals = checker.calculate_totals(statuses)

        # Output based on format
        if args.json:
            output_json(statuses, totals)
        elif args.summary:
            print_summary(statuses, totals)
        else:
            print_status_report(statuses, totals, args.health)

    except KeyboardInterrupt:
        print(f"\n{Color.WARNING}Cancelled by user{Color.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Color.FAIL}Error: {e}{Color.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
