#!/usr/bin/env python3
"""Check job status in the database"""

import boto3
import json
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

# Query recent jobs
sql = """
    SELECT
        id,
        clerk_user_id,
        job_type,
        status,
        error_message,
        created_at,
        started_at,
        completed_at,
        updated_at
    FROM jobs
    ORDER BY created_at DESC
    LIMIT 10
"""

try:
    response = rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=sql
    )

    print("📊 Recent Jobs:")
    print("=" * 100)

    if not response.get('records'):
        print("No jobs found")
    else:
        for record in response['records']:
            job_id = record[0]['stringValue']
            user_id = record[1]['stringValue']
            job_type = record[2]['stringValue']
            status = record[3]['stringValue']
            error = record[4].get('stringValue', 'None') if record[4].get('stringValue') else 'None'
            created = record[5]['stringValue']
            started = record[6].get('stringValue', 'None') if record[6].get('stringValue') else 'None'
            completed = record[7].get('stringValue', 'None') if record[7].get('stringValue') else 'None'
            updated = record[8]['stringValue']

            print(f"\nJob ID: {job_id}")
            print(f"User: {user_id}")
            print(f"Type: {job_type}")
            print(f"Status: {status}")
            print(f"Error: {error}")
            print(f"Created: {created}")
            print(f"Started: {started}")
            print(f"Completed: {completed}")
            print(f"Updated: {updated}")
            print("-" * 100)

except Exception as e:
    print(f"❌ Error querying database: {e}")
    import traceback
    traceback.print_exc()
