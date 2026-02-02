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
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import module definitions
sys.path.insert(0, str(Path(__file__).parent))
try:
    from module_definitions import MODULE_TIMEOUTS
except ImportError:
    # Fallback if module_definitions not available
    MODULE_TIMEOUTS = {}


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


def run_command(cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = False, check: bool = True, verbose: bool = False, timeout: Optional[int] = None) -> Optional[str]:
    """
    Run a command and handle errors properly.

    Args:
        cmd: Command to run
        cwd: Working directory
        capture_output: Capture stdout/stderr
        check: Check return code
        verbose: Print full output on errors
        timeout: Timeout in seconds (None = no timeout)

    Returns:
        str: stdout if capture_output=True and successful
        "success": if not capturing output and successful
        None: if command failed or timed out
    """
    try:
        if capture_output:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
            if check and result.returncode != 0:
                print(f"\n❌ Command failed: {' '.join(cmd)}")
                print(f"   Return code: {result.returncode}")
                if result.stderr:
                    print(f"   Error output:")
                    stderr_lines = result.stderr.strip().split('\n')
                    for line in stderr_lines[:10]:  # First 10 lines
                        print(f"     {line}")
                    if len(stderr_lines) > 10:
                        print(f"     ... (truncated, {len(stderr_lines)-10} more lines)")
                if verbose and result.stderr:
                    print(f"\n   Full error:\n{result.stderr}")
                return None
            return result.stdout.strip()
        else:
            result = subprocess.run(cmd, cwd=cwd, timeout=timeout)
            if check and result.returncode != 0:
                print(f"❌ Command failed with code {result.returncode}: {' '.join(cmd)}")
                return None
            return "success"
    except subprocess.TimeoutExpired:
        timeout_mins = timeout // 60 if timeout else 0
        print(f"❌ Command timed out after {timeout_mins} minutes: {' '.join(cmd)}")
        return None


def get_terraform_dir(module: str) -> Path:
    """Get the terraform directory path for a module."""
    return Path(__file__).parent.parent / "terraform" / module


def check_module_deployed(module: str) -> bool:
    """Check if a terraform module is currently deployed with validation."""
    terraform_dir = get_terraform_dir(module)
    state_file = terraform_dir / "terraform.tfstate"

    if not state_file.exists():
        return False

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)

        # Validate state structure
        if not isinstance(state, dict):
            print(f"⚠️  {module}: Invalid state file format")
            return False

        # Check terraform version (basic validation)
        if "version" not in state:
            print(f"⚠️  {module}: State file missing version field")
            return False

        resources = state.get("resources", [])

        # Empty state is suspicious
        if len(resources) == 0 and state.get("version", 0) > 0:
            print(f"⚠️  {module}: State file exists but has 0 resources")
            return False

        return len(resources) > 0

    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  {module}: Corrupted state file ({e})")
        return False


def load_last_state() -> Optional[Dict]:
    """Load the last saved destruction state with validation."""
    state_file = Path(__file__).parent / ".last_state.json"

    if not state_file.exists():
        return None

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)

        # Validate structure
        if not isinstance(state, dict):
            print("⚠️  State file corrupted (invalid format) - ignoring")
            return None
        if "destroyed_modules" not in state or "timestamp" not in state:
            print("⚠️  State file incomplete (missing keys) - ignoring")
            return None
        if not isinstance(state["destroyed_modules"], list):
            print("⚠️  State file corrupted (invalid modules list) - ignoring")
            return None

        return state
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  State file corrupted ({e}) - ignoring")
        return None


def pre_flight_check(modules: List[str]) -> Tuple[List[str], List[str]]:
    """
    Pre-flight check: verify all modules are ready to deploy.

    Returns:
        Tuple[List[str], List[str]]: (ready_modules, issues_found)
    """
    ready = []
    issues = []

    for module in modules:
        terraform_dir = get_terraform_dir(module)
        module_name = MODULE_INFO.get(module, {}).get("name", module)

        # Check terraform initialized
        if not (terraform_dir / ".terraform").exists():
            issues.append(f"{module_name} ({module}): Not initialized - run 'cd terraform/{module} && terraform init'")
            continue

        # Check tfvars exists
        tfvars_file = terraform_dir / "terraform.tfvars"
        if not tfvars_file.exists():
            tfvars_example = terraform_dir / "terraform.tfvars.example"
            if tfvars_example.exists():
                issues.append(f"{module_name} ({module}): Missing terraform.tfvars - copy from terraform.tfvars.example")
            else:
                issues.append(f"{module_name} ({module}): Missing terraform.tfvars")
            continue

        ready.append(module)

    return ready, issues


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

    # Get timeout for this module (default 10 minutes)
    timeout = MODULE_TIMEOUTS.get(module, 600)
    timeout_mins = timeout // 60

    print(f"   Running: {' '.join(cmd)} (timeout: {timeout_mins}min)")
    result = run_command(cmd, cwd=terraform_dir, check=False, timeout=timeout)

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
    """
    Deploy modules in dependency order, tracking success/failure.

    Returns:
        List[str]: Successfully deployed modules
    """
    # Resolve dependencies and deployment order
    modules_to_deploy = check_dependencies(modules)

    print("\n🔄 Deployment order (with dependencies):")
    for i, module in enumerate(modules_to_deploy, 1):
        info = MODULE_INFO.get(module, {})
        is_deployed = check_module_deployed(module)
        status = "already deployed" if is_deployed else "will deploy"
        print(f"   {i}. {info.get('name', module)} ({module}) - {status}")

    deployed_successfully = []
    failed_modules = []

    for module in modules_to_deploy:
        # Check if dependencies succeeded
        info = MODULE_INFO.get(module, {})
        dependencies = info.get("dependencies", [])

        failed_deps = [dep for dep in dependencies if dep in failed_modules]
        if failed_deps:
            print(f"\n⚠️  Skipping {module} - dependency failed: {', '.join(failed_deps)}")
            failed_modules.append(module)

            # Show which dependent modules will also be skipped
            affected = [m for m in modules_to_deploy if module in MODULE_INFO.get(m, {}).get("dependencies", [])]
            if affected:
                print(f"   ⚠️  Dependent modules that will be skipped:")
                for m in affected:
                    print(f"      • {m}")
            continue

        # Check if already deployed
        if check_module_deployed(module):
            print(f"\n✓ {module} already deployed - skipping")
            deployed_successfully.append(module)
            continue

        # Deploy module
        print(f"\n{'='*70}")
        print(f"Deploying: {module}")
        print(f"{'='*70}")

        success = deploy_module(module, auto_approve)

        if success:
            deployed_successfully.append(module)
        else:
            failed_modules.append(module)
            print(f"\n❌ Failed to deploy {module}")

            # Show which dependent modules will be skipped
            affected = [m for m in modules_to_deploy[modules_to_deploy.index(module)+1:]
                       if module in MODULE_INFO.get(m, {}).get("dependencies", [])]
            if affected:
                print(f"⚠️  The following modules depend on {module} and will be skipped:")
                for m in affected:
                    print(f"   • {m}")

    # Summary
    if failed_modules:
        print(f"\n⚠️  Deployment completed with failures:")
        print(f"   ✅ Successful: {len(deployed_successfully)}")
        print(f"   ❌ Failed: {len(failed_modules)}")

    return deployed_successfully


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

    # Pre-flight check: verify modules are ready
    print("\n🔍 Pre-flight check...")
    ready, issues = pre_flight_check(modules_to_deploy)

    if issues:
        print("\n❌ Configuration Issues Found:\n")
        for issue in issues:
            print(f"  • {issue}")
        print(f"\nFix these issues before deploying.")
        sys.exit(1)

    print(f"✓ All {len(ready)} modules ready to deploy\n")

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

    # Check if database needs seeding and ARN sync
    if "5_database" in deployed_modules:
        print("\n" + "="*70)
        print("⚠️  CRITICAL: Database ARNs Have Changed!")
        print("="*70)
        print("\n📋 CHOOSE ONE OF THESE OPTIONS:\n")
        print("1. For Dev Workflow:")
        print("   Run: python3 kb_start.py")
        print("   (Auto-syncs ARNs + starts services)\n")
        print("2. For Manual Sync Only:")
        print("   Run: uv run scripts/sync_arns.py\n")
        print("3. For Agent Deployment:")
        print("   ARN sync required before deploying agents (6_agents)")
        print("   The script will fail with 'AccessDenied' if ARNs are stale\n")
        print("📌 Then seed database: cd backend/database && uv run seed_data.py")
        print("="*70 + "\n")

    # Show cost reminder
    print("\n💰 Cost Reminder:")
    print("   Remember to run minimize_costs.py when done working")
    print("   uv run scripts/minimize_costs.py --mode shutdown")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
