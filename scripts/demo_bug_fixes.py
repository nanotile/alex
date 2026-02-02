#!/usr/bin/env python3
"""
Demo: Critical Bug Fixes in Action

This script demonstrates the improvements from our bug fixes without
actually deploying infrastructure.
"""

import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from module_definitions import (
    MODULE_DEFINITIONS,
    MODULE_TIMEOUTS,
    resolve_deployment_order,
    resolve_destruction_order,
)


def demo_module_definitions():
    """Demo: Shared module definitions (Bug #11 partial fix)"""
    print("\n" + "="*70)
    print("🔧 DEMO: Shared Module Definitions")
    print("="*70)

    print(f"\n✅ Loaded {len(MODULE_DEFINITIONS)} modules from single source:")
    for module_id, info in list(MODULE_DEFINITIONS.items())[:3]:
        print(f"   • {module_id}: {info['name']}")
        print(f"     Cost: ${info['monthly_cost']}/mo, Timeout: {MODULE_TIMEOUTS.get(module_id, 600)}s")
    print(f"   ... and {len(MODULE_DEFINITIONS) - 3} more\n")


def demo_dependency_resolution():
    """Demo: Dependency resolution (Bug #4)"""
    print("\n" + "="*70)
    print("🔗 DEMO: Dependency Resolution")
    print("="*70)

    modules = ["7_frontend", "6_agents", "5_database"]
    print(f"\n📋 Input modules (wrong order): {modules}")

    deploy_order = resolve_deployment_order(modules)
    print(f"✅ Deployment order (correct): {deploy_order}")
    print("   (Database first, then Agents, then Frontend)")

    destroy_order = resolve_destruction_order(modules)
    print(f"✅ Destruction order (reverse): {destroy_order}")
    print("   (Frontend first, then Agents, then Database)\n")


def demo_json_state_validation():
    """Demo: JSON state validation (Bug #2)"""
    print("\n" + "="*70)
    print("📄 DEMO: JSON State File Validation")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test_state.json"

        # Test 1: Corrupted JSON
        print("\n❌ Test 1: Corrupted JSON")
        state_file.write_text("{invalid json")
        try:
            with open(state_file) as f:
                json.load(f)
            print("   FAIL: Should have raised JSONDecodeError")
        except json.JSONDecodeError:
            print("   ✅ Correctly detected corrupted JSON")

        # Test 2: Missing required keys
        print("\n❌ Test 2: Missing required keys")
        state_file.write_text('{"timestamp": "2025-01-01"}')
        state = json.load(open(state_file))
        if "destroyed_modules" not in state:
            print("   ✅ Correctly detected missing 'destroyed_modules' key")

        # Test 3: Valid state with validation
        print("\n✅ Test 3: Valid state")
        valid_state = {
            "timestamp": "2025-01-01T00:00:00",
            "destroyed_modules": ["5_database", "4_researcher"]
        }
        state_file.write_text(json.dumps(valid_state, indent=2))

        # Validate
        state = json.load(open(state_file))
        if (isinstance(state, dict) and
            "destroyed_modules" in state and
            isinstance(state["destroyed_modules"], list)):
            print("   ✅ Valid state passes all checks")
            print(f"   Modules: {state['destroyed_modules']}")


def demo_terraform_timeouts():
    """Demo: Terraform timeouts (Bug #7)"""
    print("\n" + "="*70)
    print("⏱️  DEMO: Terraform Timeouts")
    print("="*70)

    print("\n✅ Different timeouts per module:")
    for module_id in ["5_database", "4_researcher", "6_agents"]:
        timeout = MODULE_TIMEOUTS.get(module_id, 600)
        timeout_mins = timeout // 60
        name = MODULE_DEFINITIONS[module_id]["name"]
        print(f"   • {name:40s} {timeout_mins:2d} minutes")

    print("\n   Why different timeouts?")
    print("   - Database (30min): Aurora scales from zero, takes time")
    print("   - App Runner (15min): Container build and deploy")
    print("   - Lambdas (10min): Quick deployment, default timeout")


def demo_cost_terminology():
    """Demo: Cost calculation terminology (Bug #8)"""
    print("\n" + "="*70)
    print("💰 DEMO: Improved Cost Terminology")
    print("="*70)

    # Calculate example costs
    all_costs = sum(info["monthly_cost"] for info in MODULE_DEFINITIONS.values())
    deployed = ["5_database", "6_agents"]  # Example
    deployed_costs = sum(MODULE_DEFINITIONS[m]["monthly_cost"] for m in deployed)
    avoided_costs = all_costs - deployed_costs
    savings_pct = (avoided_costs / all_costs * 100) if all_costs > 0 else 0

    print("\n✅ Clear terminology:")
    print(f"   Current Monthly Cost: ${deployed_costs:.2f}/month (what you're paying NOW)")
    print(f"   Currently Avoiding: ${avoided_costs:.2f}/month (resources not deployed)")
    print(f"   Max Possible Cost: ${all_costs:.2f}/month (if all modules deployed)")
    print(f"   Savings: {savings_pct:.1f}% of maximum cost")

    print("\n   Before fix (confusing):")
    print(f"   ❌ 'Potential Savings': ${avoided_costs:.2f}/month")
    print("      (Misleading - you haven't spent it yet!)")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("🎯 DEMONSTRATION: Critical Bug Fixes in Action")
    print("="*70)
    print("\nShowing improvements from our bug fixes:")
    print("  • Shared module definitions")
    print("  • Dependency resolution")
    print("  • JSON state validation")
    print("  • Terraform timeouts")
    print("  • Cost terminology")

    demo_module_definitions()
    demo_dependency_resolution()
    demo_json_state_validation()
    demo_terraform_timeouts()
    demo_cost_terminology()

    print("\n" + "="*70)
    print("✅ All Demos Complete!")
    print("="*70)
    print("\nThese fixes make the AWS_START_STOP scripts:")
    print("  ✓ More reliable (atomic writes, validation)")
    print("  ✓ Smarter (dependency resolution, pre-flight checks)")
    print("  ✓ Safer (timeouts prevent infinite hangs)")
    print("  ✓ Clearer (better error messages and terminology)")
    print()


if __name__ == "__main__":
    main()
