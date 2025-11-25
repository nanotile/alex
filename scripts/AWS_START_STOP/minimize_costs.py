#!/usr/bin/env python3
"""
Cost Minimization Script for Alex AWS Infrastructure

This script helps minimize AWS costs by intelligently destroying high-cost resources
while preserving low-cost or zero-cost infrastructure.

Usage:
    uv run scripts/minimize_costs.py --status          # Check current costs
    uv run scripts/minimize_costs.py --mode shutdown   # Destroy Aurora + App Runner
    uv run scripts/minimize_costs.py --mode minimal    # Destroy all expensive resources
    uv run scripts/minimize_costs.py --mode full       # Destroy everything
    uv run scripts/minimize_costs.py --dry-run         # Preview actions without executing
"""

import subprocess
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# Cost estimates (monthly) for each terraform module
COST_ESTIMATES = {
    "5_database": {
        "name": "Aurora Serverless v2",
        "monthly_cost": 65,
        "hourly_cost": 0.09,
        "description": "PostgreSQL database (0.5-1 ACU)",
        "priority": 1,
    },
    "4_researcher": {
        "name": "App Runner Service",
        "monthly_cost": 51,
        "hourly_cost": 0.071,
        "description": "Research agent container (1vCPU, 2GB)",
        "priority": 2,
    },
    "2_sagemaker": {
        "name": "SageMaker Serverless",
        "monthly_cost": 10,  # Estimated based on usage
        "hourly_cost": 0,
        "description": "Embedding endpoint (pay-per-use)",
        "priority": 3,
    },
    "8_enterprise": {
        "name": "CloudWatch Dashboards",
        "monthly_cost": 6,
        "hourly_cost": 0,
        "description": "Monitoring dashboards (2 dashboards)",
        "priority": 4,
    },
    "7_frontend": {
        "name": "Frontend Infrastructure",
        "monthly_cost": 2,  # Mostly pay-per-use
        "hourly_cost": 0,
        "description": "CloudFront + S3 + API Gateway (pay-per-use)",
        "priority": 5,
    },
    "6_agents": {
        "name": "Lambda Agents",
        "monthly_cost": 1,  # Pay per invocation
        "hourly_cost": 0,
        "description": "5 Lambda functions + SQS (pay-per-use)",
        "priority": 6,
    },
    "3_ingestion": {
        "name": "Ingestion Pipeline",
        "monthly_cost": 1,
        "hourly_cost": 0,
        "description": "Lambda + API Gateway (pay-per-use)",
        "priority": 7,
    },
}


# Destruction modes with different strategies
DESTRUCTION_MODES = {
    "shutdown": {
        "description": "Destroy high-cost resources (Aurora + App Runner)",
        "modules": ["5_database", "4_researcher"],
        "savings": 116,  # $65 + $51
        "keep_running": "Lambdas, S3, CloudFront, API Gateway",
    },
    "minimal": {
        "description": "Destroy all expensive resources, keep zero-cost infrastructure",
        "modules": ["8_enterprise", "7_frontend", "6_agents", "5_database", "4_researcher", "2_sagemaker"],
        "savings": 135,
        "keep_running": "S3 buckets, IAM roles (data preserved)",
    },
    "full": {
        "description": "Destroy everything (complete teardown)",
        "modules": ["8_enterprise", "7_frontend", "6_agents", "5_database", "4_researcher", "3_ingestion", "2_sagemaker"],
        "savings": 136,
        "keep_running": "Nothing (S3 data preserved unless force-deleted)",
    },
}


def run_command(cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = False, check: bool = True) -> Optional[str]:
    """Run a command and optionally capture output."""
    if capture_output:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if check and result.returncode != 0:
            return None
        return result.stdout.strip()
    else:
        result = subprocess.run(cmd, cwd=cwd)
        if check and result.returncode != 0:
            return None
        return "success"


def get_terraform_dir(module: str) -> Path:
    """Get the terraform directory path for a module."""
    return Path(__file__).parent.parent / "terraform" / module


def check_module_deployed(module: str) -> Tuple[bool, int]:
    """Check if a terraform module is deployed and count resources."""
    terraform_dir = get_terraform_dir(module)
    state_file = terraform_dir / "terraform.tfstate"

    if not state_file.exists():
        return False, 0

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
            resources = state.get("resources", [])
            return len(resources) > 0, len(resources)
    except (json.JSONDecodeError, KeyError):
        return False, 0


def get_current_status() -> Dict:
    """Get the current deployment status and cost estimate."""
    status = {
        "deployed_modules": [],
        "total_resources": 0,
        "estimated_monthly_cost": 0,
        "estimated_daily_cost": 0,
    }

    for module, cost_info in COST_ESTIMATES.items():
        is_deployed, resource_count = check_module_deployed(module)
        if is_deployed:
            status["deployed_modules"].append({
                "module": module,
                "name": cost_info["name"],
                "resources": resource_count,
                "monthly_cost": cost_info["monthly_cost"],
                "description": cost_info["description"],
            })
            status["total_resources"] += resource_count
            status["estimated_monthly_cost"] += cost_info["monthly_cost"]

    status["estimated_daily_cost"] = round(status["estimated_monthly_cost"] / 30, 2)

    return status


def print_status(status: Dict):
    """Print the current deployment status."""
    print("\n" + "=" * 70)
    print("📊 CURRENT AWS INFRASTRUCTURE STATUS")
    print("=" * 70)

    if not status["deployed_modules"]:
        print("\n✅ No resources currently deployed - minimal costs!")
        print("   (Only S3 storage charges apply)")
        return

    print(f"\n🏗️  Total Resources Deployed: {status['total_resources']}")
    print(f"💰 Estimated Monthly Cost: ${status['estimated_monthly_cost']}/month")
    print(f"📅 Estimated Daily Cost: ${status['estimated_daily_cost']}/day")

    print("\n📦 Deployed Modules:")
    for module_info in status["deployed_modules"]:
        cost_str = f"${module_info['monthly_cost']}/mo" if module_info['monthly_cost'] > 0 else "pay-per-use"
        print(f"   • {module_info['name']:30s} ({module_info['resources']:2d} resources) - {cost_str}")
        print(f"     └─ {module_info['description']}")

    print("\n" + "=" * 70)


def print_savings_analysis(mode: str):
    """Print potential savings for a destruction mode."""
    mode_info = DESTRUCTION_MODES[mode]

    print("\n" + "=" * 70)
    print(f"💡 COST SAVINGS ANALYSIS - {mode.upper()} MODE")
    print("=" * 70)

    print(f"\n📝 Strategy: {mode_info['description']}")
    print(f"💰 Estimated Monthly Savings: ${mode_info['savings']}/month")
    print(f"📅 Daily Savings: ${round(mode_info['savings'] / 30, 2)}/day")

    print("\n🗑️  Resources to Destroy:")
    total_resources = 0
    for module in mode_info["modules"]:
        is_deployed, resource_count = check_module_deployed(module)
        if is_deployed:
            cost_info = COST_ESTIMATES[module]
            cost_str = f"${cost_info['monthly_cost']}/mo" if cost_info['monthly_cost'] > 0 else "pay-per-use"
            print(f"   • {cost_info['name']:30s} ({resource_count:2d} resources) - {cost_str}")
            total_resources += resource_count
        else:
            cost_info = COST_ESTIMATES[module]
            print(f"   • {cost_info['name']:30s} (not deployed) - skip")

    print(f"\n   Total resources to destroy: {total_resources}")
    print(f"\n✅ Keep Running: {mode_info['keep_running']}")

    print("\n" + "=" * 70)


def save_state(modules_destroyed: List[str]):
    """Save the state of destroyed modules for later restoration."""
    state_file = Path(__file__).parent / ".last_state.json"
    state = {
        "timestamp": datetime.now().isoformat(),
        "destroyed_modules": modules_destroyed,
    }

    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"\n💾 State saved to {state_file}")


def destroy_module(module: str, auto_approve: bool = False) -> bool:
    """Destroy a single terraform module."""
    terraform_dir = get_terraform_dir(module)

    if not terraform_dir.exists():
        print(f"   ⚠️  Directory not found: {terraform_dir}")
        return False

    if not (terraform_dir / ".terraform").exists():
        print(f"   ⚠️  Terraform not initialized in {module}")
        return False

    is_deployed, resource_count = check_module_deployed(module)
    if not is_deployed:
        print(f"   ℹ️  Module {module} not deployed, skipping...")
        return True

    cost_info = COST_ESTIMATES.get(module, {})
    print(f"\n🗑️  Destroying: {cost_info.get('name', module)} ({resource_count} resources)")

    # Build terraform destroy command
    cmd = ["terraform", "destroy"]
    if auto_approve:
        cmd.append("-auto-approve")

    print(f"   Running: {' '.join(cmd)}")
    result = run_command(cmd, cwd=terraform_dir, check=False)

    if result:
        print(f"   ✅ Module {module} destroyed successfully")
        return True
    else:
        print(f"   ❌ Failed to destroy module {module}")
        return False


def destroy_with_dependencies(modules: List[str], auto_approve: bool = False) -> List[str]:
    """Destroy modules in the correct order to handle dependencies."""
    # Define safe destruction order (reverse of creation)
    destruction_order = [
        "8_enterprise",   # No dependencies
        "7_frontend",     # Depends on 6_agents, 5_database
        "6_agents",       # Depends on 5_database
        "5_database",     # Independent (but agents depend on it)
        "4_researcher",   # Independent
        "3_ingestion",    # Independent (but agents may use it)
        "2_sagemaker",    # Independent (but ingestion uses it)
    ]

    # Filter to only modules we want to destroy, in the correct order
    modules_to_destroy = [m for m in destruction_order if m in modules]
    destroyed_modules = []

    print("\n🔄 Destruction order (handling dependencies):")
    for i, module in enumerate(modules_to_destroy, 1):
        cost_info = COST_ESTIMATES.get(module, {})
        print(f"   {i}. {cost_info.get('name', module)} ({module})")

    for module in modules_to_destroy:
        success = destroy_module(module, auto_approve)
        if success:
            destroyed_modules.append(module)

    return destroyed_modules


def confirm_destruction(mode: str) -> bool:
    """Ask for confirmation before destroying resources."""
    mode_info = DESTRUCTION_MODES[mode]

    print("\n" + "=" * 70)
    print("⚠️  WARNING: INFRASTRUCTURE DESTRUCTION")
    print("=" * 70)

    print(f"\nYou are about to destroy resources in {mode.upper()} mode:")
    print(f"   {mode_info['description']}")
    print(f"\n💰 Estimated savings: ${mode_info['savings']}/month")
    print(f"📦 Modules to destroy: {len(mode_info['modules'])}")

    # Check which modules are actually deployed
    deployed_count = 0
    for module in mode_info["modules"]:
        is_deployed, _ = check_module_deployed(module)
        if is_deployed:
            deployed_count += 1

    print(f"🏗️  Currently deployed modules to destroy: {deployed_count}/{len(mode_info['modules'])}")

    if deployed_count == 0:
        print("\n✅ Nothing to destroy - all modules already removed!")
        return False

    print("\n⚠️  This action cannot be undone (but can be redeployed later)")
    print("\n" + "=" * 70)

    response = input("\nType 'yes' to confirm destruction: ")
    return response.lower() == 'yes'


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Minimize AWS costs for Alex infrastructure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check current status and costs
  uv run scripts/minimize_costs.py --status

  # Destroy expensive resources (Aurora + App Runner)
  uv run scripts/minimize_costs.py --mode shutdown

  # Preview shutdown without executing
  uv run scripts/minimize_costs.py --mode shutdown --dry-run

  # Destroy everything
  uv run scripts/minimize_costs.py --mode full --auto-approve
        """
    )

    parser.add_argument("--status", action="store_true", help="Show current deployment status and costs")
    parser.add_argument("--mode", choices=["shutdown", "minimal", "full"], help="Destruction mode")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be destroyed without executing")
    parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")

    args = parser.parse_args()

    print("\n💰 Alex Infrastructure Cost Minimization Tool")
    print("=" * 70)

    # Get current status
    status = get_current_status()

    # If --status flag, just show status and exit
    if args.status or (not args.mode and not args.dry_run):
        print_status(status)

        if status["estimated_monthly_cost"] > 0:
            print("\n💡 TIP: To reduce costs, use one of these modes:")
            print("   --mode shutdown  (save ~$116/mo, keep Lambdas/S3/CloudFront)")
            print("   --mode minimal   (save ~$135/mo, keep S3 data)")
            print("   --mode full      (save ~$136/mo, destroy everything)")

        return

    if not args.mode:
        print("❌ Error: --mode is required")
        parser.print_help()
        sys.exit(1)

    # Show savings analysis
    print_savings_analysis(args.mode)

    # Dry run mode - just show what would happen
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
        print("\nTo execute this destruction, run without --dry-run:")
        print(f"   uv run scripts/minimize_costs.py --mode {args.mode}")
        return

    # Confirm destruction
    if not args.auto_approve:
        if not confirm_destruction(args.mode):
            print("\n❌ Destruction cancelled")
            return

    # Execute destruction
    mode_info = DESTRUCTION_MODES[args.mode]
    destroyed_modules = destroy_with_dependencies(mode_info["modules"], args.auto_approve)

    # Save state for restoration
    if destroyed_modules:
        save_state(destroyed_modules)

    # Show final status
    print("\n" + "=" * 70)
    print("✅ DESTRUCTION COMPLETE")
    print("=" * 70)

    print(f"\n🗑️  Destroyed {len(destroyed_modules)} modules:")
    for module in destroyed_modules:
        cost_info = COST_ESTIMATES.get(module, {})
        print(f"   • {cost_info.get('name', module)}")

    # Show new status
    new_status = get_current_status()
    print(f"\n💰 New estimated monthly cost: ${new_status['estimated_monthly_cost']}/month")
    print(f"📉 Monthly savings: ${status['estimated_monthly_cost'] - new_status['estimated_monthly_cost']}/month")

    print("\n💡 To restore infrastructure later:")
    print("   uv run scripts/restart_infrastructure.py")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
