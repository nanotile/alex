#!/usr/bin/env python3
"""Check the most recent analysis job"""

import boto3
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Get environment variables
cluster_arn = os.getenv('AURORA_CLUSTER_ARN')
secret_arn = os.getenv('AURORA_SECRET_ARN')
database_name = os.getenv('AURORA_DATABASE_NAME', 'alex')
region = os.getenv('DEFAULT_AWS_REGION', 'us-east-1')

# Create RDS Data client
rds_data = boto3.client('rds-data', region_name=region)

# Query most recent job
sql = """
    SELECT
        id,
        clerk_user_id,
        job_type,
        status,
        created_at,
        completed_at
    FROM jobs
    ORDER BY created_at DESC
    LIMIT 1
"""

try:
    response = rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=sql
    )

    if response.get('records'):
        record = response['records'][0]
        job_id = record[0]['stringValue']
        user_id = record[1]['stringValue']
        job_type = record[2]['stringValue']
        status = record[3]['stringValue']
        created = record[4]['stringValue']
        completed = record[5].get('stringValue', 'Not completed') if record[5].get('stringValue') else 'Not completed'

        print("\n" + "="*80)
        print("📊 MOST RECENT ANALYSIS JOB")
        print("="*80)
        print(f"\n  Job ID:    {job_id}")
        print(f"  User:      {user_id}")
        print(f"  Type:      {job_type}")
        print(f"  Status:    {status}")
        print(f"  Created:   {created}")
        print(f"  Completed: {completed}")

        if status == 'completed':
            print(f"\n  ✅ Analysis complete!")
            print(f"\n  📎 View results at:")
            print(f"     http://localhost:3000/analysis?job_id={job_id}")
        elif status == 'pending':
            print(f"\n  ⏳ Analysis still pending...")
        elif status == 'running':
            print(f"\n  🔄 Analysis in progress...")
        elif status == 'failed':
            print(f"\n  ❌ Analysis failed")

        print("\n" + "="*80 + "\n")
    else:
        print("No jobs found")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
