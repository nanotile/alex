#!/usr/bin/env python3
"""
Cost Minimization Script for Alex AWS Infrastructure - ENHANCED V2
Now includes live AWS API checks for 'ghost' resources and orphaned snapshots.
minimize_costs.py
https://gemini.google.com/app/d1c3baee2fdcf7a8
Requires: boto3 (pip install boto3)
This script extends the original cost minimization tool by querying live AWS APIs
to identify resources that may not be tracked by Terraform, such as manual snapshots
or OpenSearch Serverless collections. It provides a more comprehensive overview of
potential cost-saving opportunities.
Author: ChatGPT-4
Date: 2025-12-30
"""

import subprocess
import sys
import json
import argparse
import boto3  # Required: pip install boto3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# --- CONFIGURATION ---
REGIONS = ["us-east-1", "us-west-2"] # Add regions you use
# Cost estimates (monthly) - Added OpenSearch/Bedrock
COST_ESTIMATES = {
    "9_opensearch": {
        "name": "OpenSearch Serverless",
        "monthly_cost": 175,
        "description": "Vector store (OCUs) - High priority to kill",
        "priority": 0,
    },
    "5_database": {
        "name": "Aurora Serverless v2",
        "monthly_cost": 65,
        "hourly_cost": 0.12,
        "description": "PostgreSQL database (0.5-1 ACU)",
        "priority": 1,
    },
    # ... (rest of your existing COST_ESTIMATES)
}

class AWSHunter:
    """Queries live AWS APIs to find resources that Terraform might have missed."""
    
    def __init__(self, regions: List[str]):
        self.regions = regions

    def get_live_orphans(self) -> List[Dict]:
        orphans = []
        for region in self.regions:
            # 1. Check for Aurora Clusters
            rds = boto3.client('rds', region_name=region)
            clusters = rds.describe_db_clusters()['DBClusters']
            for c in clusters:
                orphans.append({
                    "region": region,
                    "type": "Aurora Cluster",
                    "id": c['DBClusterIdentifier'],
                    "status": c['Status']
                })

            # 2. Check for Manual Snapshots (The $26.85 culprit)
            snapshots = rds.describe_db_cluster_snapshots(SnapshotType='manual')['DBClusterSnapshots']
            for s in snapshots:
                orphans.append({
                    "region": region,
                    "type": "Manual Snapshot",
                    "id": s['DBClusterSnapshotIdentifier'],
                    "status": "Stored"
                })

            # 3. Check for OpenSearch Serverless (Bedrock Ghost)
            oss = boto3.client('opensearchserverless', region_name=region)
            try:
                collections = oss.list_collections()['collectionSummaries']
                for col in collections:
                    orphans.append({
                        "region": region,
                        "type": "OpenSearch Collection",
                        "id": col['name'],
                        "status": col['status']
                    })
            except: pass # Service might not be active
            
        return orphans

def get_current_status(hunter: AWSHunter) -> Dict:
    """Enhanced status including Live AWS scan."""
    status = {
        "deployed_modules": [],
        "orphans": hunter.get_live_orphans(),
        "total_resources": 0,
        "estimated_monthly_cost": 0,
    }

    # Your original Terraform check logic
    for module, cost_info in COST_ESTIMATES.items():
        # ... (keep your existing check_module_deployed logic here)
        pass

    return status

def print_status(status: Dict):
    """Print the current deployment status with high-visibility warnings."""
    print("\n" + "=" * 70)
    print("📊 CURRENT AWS INFRASTRUCTURE STATUS (LIVE SCAN)")
    print("=" * 70)

    # Display Ghost Resources FIRST
    if status["orphans"]:
        print("\n⚠️  WARNING: UNMANAGED 'GHOST' RESOURCES FOUND!")
        print("   These exist in AWS but may not be tracked by Terraform:")
        for o in status["orphans"]:
            print(f"   🔴 [{o['region']}] {o['type']}: {o['id']} ({o['status']})")
    else:
        print("\n✅ No orphaned AWS resources detected.")

    # ... (rest of your existing print_status logic)

def destroy_module(module: str, auto_approve: bool = False) -> bool:
    """Enhanced destroy: Forces no snapshots to ensure cost hits $0."""
    terraform_dir = get_terraform_dir(module)
    
    # Force 'skip_final_snapshot' if your TF variable supports it
    cmd = ["terraform", "destroy", "-var", "skip_final_snapshot=true"]
    if auto_approve:
        cmd.append("-auto-approve")
        
    # ... (rest of your existing run_command logic)

# ... (rest of your original script logic for main, confirm_destruction, etc.)