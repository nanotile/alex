#!/usr/bin/env python3
import subprocess
import sys
import os
import json
import argparse  # Added for flag handling
from pathlib import Path

# ... (keep existing run_command, check_prerequisites, etc.) ...

def minimize_costs_teardown():
    """
    https://gemini.google.com/app/d1c3baee2fdcf7a8
    Destroys the infrastructure while ensuring no expensive 
    final snapshots are created for the Aurora database.
    """
    print("\n💸 Starting Cost-Minimization Teardown...")
    
    terraform_dir = Path(__file__).parent.parent / "terraform" / "7_frontend"
    
    if not terraform_dir.exists():
        print(f"  ❌ Terraform directory not found: {terraform_dir}")
        sys.exit(1)

    # Force skip_final_snapshot to true during destruction 
    cmd = [
        "terraform", "destroy", 
        "-auto-approve", 
        "-var", "skip_final_snapshot=true"
    ]
    
    run_command(cmd, cwd=terraform_dir)
    print("\n✅ Infrastructure destroyed. Final snapshots were skipped to save costs.")

def main():
    """Updated main function with teardown support."""
    parser = argparse.ArgumentParser(description="Alex Financial Advisor Deployment Tool")
    parser.add_argument("--teardown", action="store_true", help="Destroy infrastructure cheaply")
    
    # Use parse_known_args to allow coexistence with your existing logic
    args, unknown = parser.parse_known_args()

    if args.teardown:
        minimize_costs_teardown()
        return

    print("🚀 Alex Financial Advisor - Part 7 Deployment")
    print("=" * 50)

    # ... (rest of your existing deployment logic: package_lambda, deploy_terraform, etc.) ...

    # ... (rest of your existing deployment logic: package_lambda, deploy_terraform, etc.) ..