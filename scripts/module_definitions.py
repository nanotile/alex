#!/usr/bin/env python3
"""
Shared Module Definitions for AWS_START_STOP Scripts

Single source of truth for all AWS terraform module metadata used by:
- deployment_status.py
- minimize_costs.py
- restart_infrastructure.py

This ensures consistency across all cost management and deployment scripts.

Author: KB (Kent Benson) with Claude Code
Project: Alex - AI in Production
"""

from typing import Dict, List


# Complete module definitions combining all metadata
MODULE_DEFINITIONS = {
    "2_sagemaker": {
        "name": "SageMaker Serverless Endpoint",
        "description": "Embedding endpoint (pay-per-use)",
        "monthly_cost": 10,
        "hourly_cost": 0.014,
        "priority": 3,
        "category": "AI/ML",
        "dependencies": [],
        "requires_seed_data": False,
        "typical_deploy_time": "8-12 minutes",
        "expected_resource_count": 3,  # Endpoint, IAM role, policy
    },
    "3_ingestion": {
        "name": "Document Ingestion Pipeline",
        "description": "Lambda + API Gateway (pay-per-use)",
        "monthly_cost": 1,
        "hourly_cost": 0.001,
        "priority": 7,
        "category": "Data",
        "dependencies": ["2_sagemaker"],
        "requires_seed_data": False,
        "typical_deploy_time": "3-5 minutes",
        "expected_resource_count": 8,  # Lambda, API Gateway, S3 Vectors, IAM, etc.
    },
    "4_researcher": {
        "name": "Researcher Agent (App Runner)",
        "description": "Research agent container (1vCPU, 2GB)",
        "monthly_cost": 51,
        "hourly_cost": 0.071,
        "priority": 2,
        "category": "AI Agents",
        "dependencies": [],
        "requires_seed_data": False,
        "typical_deploy_time": "8-10 minutes",
        "expected_resource_count": 4,  # App Runner service, ECR repo, IAM roles
    },
    "5_database": {
        "name": "Aurora Serverless v2",
        "description": "PostgreSQL database (0.5-1 ACU)",
        "monthly_cost": 65,
        "hourly_cost": 0.09,
        "priority": 1,
        "category": "Database",
        "dependencies": [],
        "requires_seed_data": True,
        "typical_deploy_time": "10-15 minutes",
        "expected_resource_count": 6,  # Cluster, instances, secret, subnet group, etc.
    },
    "6_agents": {
        "name": "Lambda Agents",
        "description": "5 Lambda functions + SQS (pay-per-use)",
        "monthly_cost": 1,
        "hourly_cost": 0.001,
        "priority": 6,
        "category": "AI Agents",
        "dependencies": ["5_database"],
        "requires_seed_data": False,
        "typical_deploy_time": "5-7 minutes",
        "expected_resource_count": 15,  # 5 Lambdas + SQS + S3 bucket + IAM roles
    },
    "7_frontend": {
        "name": "Frontend Infrastructure",
        "description": "CloudFront + S3 + API Gateway (pay-per-use)",
        "monthly_cost": 2,
        "hourly_cost": 0.003,
        "priority": 5,
        "category": "Frontend",
        "dependencies": ["5_database", "6_agents"],
        "requires_seed_data": False,
        "typical_deploy_time": "10-12 minutes",
        "expected_resource_count": 10,  # CloudFront, S3, API Gateway, Lambda, etc.
    },
    "8_enterprise": {
        "name": "Enterprise Monitoring",
        "description": "CloudWatch dashboards (2 dashboards)",
        "monthly_cost": 6,
        "hourly_cost": 0.008,
        "priority": 4,
        "category": "Monitoring",
        "dependencies": [],
        "requires_seed_data": False,
        "typical_deploy_time": "2-3 minutes",
        "expected_resource_count": 4,  # 2 dashboards + alarms
    },
}


# Destruction modes for minimize_costs.py
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


# Preset deployment configurations for restart_infrastructure.py
DEPLOYMENT_PRESETS = {
    "daily": {
        "description": "Daily development setup (database + agents)",
        "modules": ["5_database", "6_agents"],
        "use_case": "Daily development work with AI agents",
        "estimated_time": "15-22 minutes",
    },
    "frontend": {
        "description": "Frontend testing setup (database + agents + frontend)",
        "modules": ["5_database", "6_agents", "7_frontend"],
        "use_case": "Testing the full user interface",
        "estimated_time": "25-34 minutes",
    },
    "research": {
        "description": "Research infrastructure (researcher + sagemaker)",
        "modules": ["2_sagemaker", "4_researcher"],
        "use_case": "Running research agent",
        "estimated_time": "13-18 minutes",
    },
    "full": {
        "description": "Complete infrastructure",
        "modules": ["2_sagemaker", "3_ingestion", "4_researcher", "5_database", "6_agents", "7_frontend", "8_enterprise"],
        "use_case": "Full production-like environment",
        "estimated_time": "40-50 minutes",
    },
}


# Terraform operation timeouts (in seconds) by module
MODULE_TIMEOUTS = {
    "5_database": 1800,     # 30 minutes for Aurora (slow to spin up)
    "4_researcher": 900,    # 15 minutes for App Runner (container build)
    "7_frontend": 900,      # 15 minutes for CloudFront (global distribution)
    "2_sagemaker": 720,     # 12 minutes for SageMaker endpoint
    "6_agents": 600,        # 10 minutes for Lambda deployment
    "8_enterprise": 300,    # 5 minutes for CloudWatch
    "3_ingestion": 300,     # 5 minutes for ingestion pipeline
}


def get_all_module_ids() -> List[str]:
    """Get list of all module IDs sorted by priority (cost impact)."""
    return sorted(
        MODULE_DEFINITIONS.keys(),
        key=lambda m: MODULE_DEFINITIONS[m]["priority"]
    )


def get_total_monthly_cost() -> float:
    """Calculate total monthly cost if all modules deployed."""
    return sum(info["monthly_cost"] for info in MODULE_DEFINITIONS.values())


def get_module_dependencies(module_id: str) -> List[str]:
    """Get list of modules that this module depends on."""
    return MODULE_DEFINITIONS.get(module_id, {}).get("dependencies", [])


def resolve_deployment_order(modules: List[str]) -> List[str]:
    """
    Resolve module deployment order based on dependencies.

    Uses topological sort to ensure dependencies are deployed before
    modules that depend on them.

    Args:
        modules: List of module IDs to deploy

    Returns:
        List of module IDs in correct deployment order

    Example:
        >>> resolve_deployment_order(["6_agents", "5_database"])
        ["5_database", "6_agents"]  # Database first, then agents
    """
    ordered = []
    remaining = set(modules)

    while remaining:
        # Find modules with all dependencies satisfied
        deployable = [
            m for m in remaining
            if all(dep in ordered or dep not in remaining
                   for dep in MODULE_DEFINITIONS.get(m, {}).get("dependencies", []))
        ]

        if not deployable:
            # Circular dependency or missing module
            # Just add remaining in arbitrary order
            ordered.extend(sorted(remaining))
            break

        # Add in priority order (highest cost first within same dependency level)
        deployable.sort(key=lambda m: MODULE_DEFINITIONS.get(m, {}).get("priority", 999))
        ordered.extend(deployable)
        remaining -= set(deployable)

    return ordered


def resolve_destruction_order(modules: List[str]) -> List[str]:
    """
    Resolve module destruction order (reverse of deployment order).

    Ensures dependent modules are destroyed before their dependencies.

    Args:
        modules: List of module IDs to destroy

    Returns:
        List of module IDs in correct destruction order

    Example:
        >>> resolve_destruction_order(["5_database", "6_agents"])
        ["6_agents", "5_database"]  # Agents first, then database
    """
    return list(reversed(resolve_deployment_order(modules)))


# Export key functions and data
__all__ = [
    "MODULE_DEFINITIONS",
    "DESTRUCTION_MODES",
    "DEPLOYMENT_PRESETS",
    "MODULE_TIMEOUTS",
    "get_all_module_ids",
    "get_total_monthly_cost",
    "get_module_dependencies",
    "resolve_deployment_order",
    "resolve_destruction_order",
]
