#!/usr/bin/env python3
"""
Infrastructure Restart Script for Alex AWS Infrastructure

This script helps restore AWS infrastructure that was previously destroyed
for cost savings. It intelligently rebuilds resources in the correct order.

Usage:
    uv run scripts/restart_infrastructure.py --all                # Restore everything from last shutdown
    uv run scripts/restart_infrastructure.py --modules 5_database # Restore specific modules
    uv run scripts/restart_infrastructure.py --preset daily       # Restore common daily-use resources
    uv run scripts/restart_infrastructure.py --status             # Check what was destroyed last
"""

import subprocess
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# Module information
MODULE_INFO = {
    "2_sagemaker": {
        "name": "SageMaker Serverless Endpoint",
        "description": "Embedding generation endpoint",
        "dependencies": [],
        "requires_seed_data": False,
        "typical_deploy_time": "5-8 minutes",
    },
    "3_ingestion": {
        "name": "Ingestion Pipeline",
        "description": "Document ingestion Lambda + API Gateway",
        "dependencies": ["2_sagemaker"],
        "requires_seed_data": False,
        "typical_deploy_time": "2-3 minutes",
    },
    "4_researcher": {
        "name": "Researcher Agent",
        "description": "App Runner research service",
        "dependencies": [],
        "requires_seed_data": False,
        "typical_deploy_time": "8-10 minutes",
    },
    "5_database": {
        "name": "Aurora Serverless v2",
        "description": "PostgreSQL database",
        "dependencies": [],
        "requires_seed_data": True,
        "typical_deploy_time": "10-15 minutes",
    },
    "6_agents": {
        "name": "Lambda Agents",
        "description": "5 AI agents + SQS orchestration",
        "dependencies": ["5_database"],
        "requires_seed_data": False,
        "typical_deploy_time": "5-7 minutes",
    },
    "7_frontend": {
        "name": "Frontend Infrastructure",
        "description": "CloudFront + S3 + API Gateway",
        "dependencies": ["5_database", "6_agents"],
        "requires_seed_data": False,
        "typical_deploy_time": "10-12 minutes",
    },
    "8_enterprise": {
        "name": "Enterprise Monitoring",
        "description": "CloudWatch dashboards and alarms",
        "dependencies": [],
        "requires_seed_data": False,
        "typical_deploy_time": "2-3 minutes",
    },
}


# Preset configurations for common scenarios
PRESETS = {
    "daily": {
        "description": "Daily development setup (database + agents)",
        "modules": ["5_database", "6_agents"],
        "use_case": "Daily development work with AI agents",
    },
    "frontend": {
        "description": "Frontend testing setup (database + agents + frontend)",
        "modules": ["5_database", "6_agents", "7_frontend"],
        "use_case": "Testing the full user interface",
    },
    "research": {
        "description": "Research infrastructure (researcher + sagemaker)",
        "modules": ["2_sagemaker", "4_researcher"],
        "use_case": "Running research agent",
    },
    "full": {
        "description": "Complete infrastructure",
        "modules": ["2_sagemaker", "3_ingestion", "4_researcher", "5_database", "6_agents", "7_frontend", "8_enterprise"],
        "use_case": "Full production-like environment",
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


def check_module_deployed(module: str) -> bool:
    """Check if a terraform module is currently deployed."""
    terraform_dir = get_terraform_dir(module)
    state_file = terraform_dir / "terraform.tfstate"

    if not state_file.exists():
        return False

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
            resources = state.get("resources", [])
            return len(resources) > 0
    except (json.JSONDecodeError, KeyError):
        return False


def load_last_state() -> Optional[Dict]:
    """Load the last saved destruction state."""
    state_file = Path(__file__).parent / ".last_state.json"

    if not state_file.exists():
        return None

    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return None


def print_last_state():
    """Print information about the last destruction."""
    state = load_last_state()

    print("\n" + "=" * 70)
    print("📋 LAST DESTRUCTION STATE")
    print("=" * 70)

    if not state:
        print("\n❌ No previous destruction state found")
        print("   (No .last_state.json file)")
        return

    timestamp = datetime.fromisoformat(state["timestamp"])
    destroyed_modules = state.get("destroyed_modules", [])

    print(f"\n🕒 Last destruction: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📦 Modules destroyed: {len(destroyed_modules)}")

    if destroyed_modules:
        print("\n🗑️  Destroyed modules:")
        for module in destroyed_modules:
            info = MODULE_INFO.get(module, {})
            name = info.get("name", module)
            is_deployed = check_module_deployed(module)
            status = "✅ now deployed" if is_deployed else "❌ still destroyed"
            print(f"   • {name:40s} {status}")

    print("\n" + "=" * 70)


def check_dependencies(modules: List[str]) -> List[str]:
    """Check if dependencies are met and add missing ones."""
    required_modules = set(modules)

    for module in modules:
        info = MODULE_INFO.get(module, {})
        dependencies = info.get("dependencies", [])
        required_modules.update(dependencies)

    # Return modules in deployment order
    return resolve_deployment_order(list(required_modules))


def resolve_deployment_order(modules: List[str]) -> List[str]:
    """Resolve the correct deployment order based on dependencies."""
    # Define deployment order (opposite of destruction)
    deployment_order = [
        "2_sagemaker",    # No dependencies
        "3_ingestion",    # Depends on sagemaker
        "4_researcher",   # No dependencies
        "5_database",     # No dependencies
        "6_agents",       # Depends on database
        "7_frontend",     # Depends on database + agents
        "8_enterprise",   # No dependencies
    ]

    # Filter to requested modules, maintaining order
    return [m for m in deployment_order if m in modules]


def check_tfvars(module: str) -> bool:
    """Check if terraform.tfvars exists for a module."""
    terraform_dir = get_terraform_dir(module)
    tfvars_file = terraform_dir / "terraform.tfvars"

    return tfvars_file.exists()


def deploy_module(module: str, auto_approve: bool = False) -> bool:
    """Deploy a single terraform module."""
    terraform_dir = get_terraform_dir(module)

    if not terraform_dir.exists():
        print(f"   ❌ Directory not found: {terraform_dir}")
        return False

    # Check if terraform.tfvars exists
    if not check_tfvars(module):
        print(f"   ⚠️  WARNING: terraform.tfvars not found in {module}")
        print(f"       Copy terraform.tfvars.example to terraform.tfvars and configure it")
        return False

    info = MODULE_INFO.get(module, {})
    print(f"\n🚀 Deploying: {info.get('name', module)}")
    print(f"   Description: {info.get('description', 'N/A')}")
    print(f"   Estimated time: {info.get('typical_deploy_time', 'unknown')}")

    # Check if already deployed
    if check_module_deployed(module):
        print(f"   ℹ️  Module {module} already deployed, skipping...")
        return True

    # Initialize terraform if needed
    if not (terraform_dir / ".terraform").exists():
        print(f"   Initializing terraform...")
        result = run_command(["terraform", "init"], cwd=terraform_dir, check=False)
        if not result:
            print(f"   ❌ Terraform init failed")
            return False

    # Build terraform apply command
    cmd = ["terraform", "apply"]
    if auto_approve:
        cmd.append("-auto-approve")

    print(f"   Running: {' '.join(cmd)}")
    result = run_command(cmd, cwd=terraform_dir, check=False)

    if result:
        print(f"   ✅ Module {module} deployed successfully")

        # Check if seed data is needed
        if info.get("requires_seed_data", False):
            print(f"\n   ⚠️  This module requires seed data!")
            print(f"       Run: cd backend/database && uv run seed_data.py")

        return True
    else:
        print(f"   ❌ Failed to deploy module {module}")
        return False


def deploy_modules(modules: List[str], auto_approve: bool = False) -> List[str]:
    """Deploy multiple modules in the correct order."""
    # Resolve dependencies and deployment order
    modules_to_deploy = check_dependencies(modules)

    print("\n🔄 Deployment order (with dependencies):")
    for i, module in enumerate(modules_to_deploy, 1):
        info = MODULE_INFO.get(module, {})
        is_deployed = check_module_deployed(module)
        status = "already deployed" if is_deployed else "will deploy"
        print(f"   {i}. {info.get('name', module)} ({module}) - {status}")

    deployed_modules = []

    for module in modules_to_deploy:
        success = deploy_module(module, auto_approve)
        if success:
            deployed_modules.append(module)
        else:
            print(f"\n⚠️  Stopping deployment due to failure in {module}")
            break

    return deployed_modules


def print_preset_info(preset_name: str):
    """Print information about a preset configuration."""
    preset = PRESETS.get(preset_name)
    if not preset:
        return

    print("\n" + "=" * 70)
    print(f"📋 PRESET: {preset_name.upper()}")
    print("=" * 70)

    print(f"\n📝 Description: {preset['description']}")
    print(f"💡 Use Case: {preset['use_case']}")

    print(f"\n📦 Modules to deploy: {len(preset['modules'])}")
    for module in preset["modules"]:
        info = MODULE_INFO.get(module, {})
        is_deployed = check_module_deployed(module)
        status = "✅ deployed" if is_deployed else "❌ not deployed"
        print(f"   • {info.get('name', module):40s} {status}")

    # Calculate total deployment time
    total_time_min = 0
    total_time_max = 0
    for module in preset["modules"]:
        if not check_module_deployed(module):
            info = MODULE_INFO.get(module, {})
            time_range = info.get("typical_deploy_time", "5-10 minutes")
            if "-" in time_range:
                min_time, max_time = time_range.split("-")
                total_time_min += int(min_time.split()[0])
                total_time_max += int(max_time.split()[0])

    if total_time_min > 0:
        print(f"\n⏱️  Estimated deployment time: {total_time_min}-{total_time_max} minutes")

    print("\n" + "=" * 70)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Restart AWS infrastructure for Alex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check what was destroyed last
  uv run scripts/restart_infrastructure.py --status

  # Restore everything from last shutdown
  uv run scripts/restart_infrastructure.py --all

  # Restore specific modules
  uv run scripts/restart_infrastructure.py --modules 5_database 6_agents

  # Use a preset configuration
  uv run scripts/restart_infrastructure.py --preset daily

  # Show available presets
  uv run scripts/restart_infrastructure.py --list-presets
        """
    )

    parser.add_argument("--status", action="store_true", help="Show last destruction state")
    parser.add_argument("--all", action="store_true", help="Restore all modules from last destruction")
    parser.add_argument("--modules", nargs="+", help="Specific modules to restore")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Use a preset configuration")
    parser.add_argument("--list-presets", action="store_true", help="List available presets")
    parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")

    args = parser.parse_args()

    print("\n🚀 Alex Infrastructure Restart Tool")
    print("=" * 70)

    # Show last state if requested
    if args.status:
        print_last_state()
        return

    # List presets if requested
    if args.list_presets:
        print("\n📋 AVAILABLE PRESETS")
        print("=" * 70)
        for preset_name, preset_info in PRESETS.items():
            print(f"\n🎯 {preset_name.upper()}")
            print(f"   Description: {preset_info['description']}")
            print(f"   Use Case: {preset_info['use_case']}")
            print(f"   Modules: {', '.join([MODULE_INFO[m]['name'] for m in preset_info['modules']])}")
        print("\n" + "=" * 70)
        return

    # Determine which modules to deploy
    modules_to_deploy = []

    if args.all:
        state = load_last_state()
        if not state:
            print("\n❌ Error: No previous destruction state found")
            print("   Use --modules to specify modules manually")
            return
        modules_to_deploy = state.get("destroyed_modules", [])
        print(f"\n📋 Restoring {len(modules_to_deploy)} modules from last destruction")

    elif args.modules:
        modules_to_deploy = args.modules
        print(f"\n📋 Restoring {len(modules_to_deploy)} specified modules")

    elif args.preset:
        preset = PRESETS[args.preset]
        modules_to_deploy = preset["modules"]
        print_preset_info(args.preset)
    else:
        print("❌ Error: Must specify --all, --modules, or --preset")
        parser.print_help()
        return

    if not modules_to_deploy:
        print("\n❌ No modules to deploy")
        return

    # Confirm deployment
    if not args.auto_approve:
        print("\n⚠️  Ready to deploy infrastructure")
        print("   This will create AWS resources and incur costs")
        response = input("\nType 'yes' to confirm deployment: ")
        if response.lower() != 'yes':
            print("\n❌ Deployment cancelled")
            return

    # Deploy modules
    deployed_modules = deploy_modules(modules_to_deploy, args.auto_approve)

    # Show final summary
    print("\n" + "=" * 70)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 70)

    print(f"\n🚀 Successfully deployed {len(deployed_modules)} modules:")
    for module in deployed_modules:
        info = MODULE_INFO.get(module, {})
        print(f"   • {info.get('name', module)}")

    # Check if database needs seeding
    if "5_database" in deployed_modules:
        print("\n⚠️  IMPORTANT: Database requires seed data!")
        print("   Run: cd backend/database && uv run seed_data.py")

    # Show cost reminder
    print("\n💰 Cost Reminder:")
    print("   Remember to run minimize_costs.py when done working")
    print("   uv run scripts/minimize_costs.py --mode shutdown")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
