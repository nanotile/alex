#!/usr/bin/env python3
"""
Check the summary_payload for execution timing data.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Import database
import sys
sys.path.append('backend/database')
from src import Database

db = Database()

job_id = "d58b197b-c2a1-4747-8610-81bd0cf26c99"

print(f"Fetching job: {job_id}\n")
job = db.jobs.find_by_id(job_id)

if not job:
    print("❌ Job not found!")
    sys.exit(1)

print(f"Job Status: {job['status']}")
print(f"Created: {job.get('created_at')}")
print(f"Updated: {job.get('updated_at')}")
print()

if job.get('summary_payload'):
    print("=" * 70)
    print("SUMMARY PAYLOAD (Execution Timing Data)")
    print("=" * 70)
    summary = job['summary_payload']
    print(json.dumps(summary, indent=2))
    print()

    if 'total_duration' in summary:
        print(f"✅ Total Duration: {summary['total_duration']}s")

    if 'agent_executions' in summary:
        print("\n✅ Agent Execution Times:")
        for agent_name, agent_data in summary['agent_executions'].items():
            duration = agent_data.get('duration', 'N/A')
            status = agent_data.get('status', 'N/A')
            print(f"   {agent_name}: {duration}s ({status})")
else:
    print("⚠️  No summary_payload found")

if job.get('error_message'):
    print(f"\n❌ Error: {job['error_message']}")
