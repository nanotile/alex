#!/usr/bin/env python3
"""Check analysis job status in the database"""

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

# Query recent analysis jobs
sql = """
    SELECT
        job_id,
        user_id,
        status,
        error_message,
        created_at,
        updated_at
    FROM analysis_jobs
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

    print("📊 Recent Analysis Jobs:")
    print("=" * 100)

    if not response.get('records'):
        print("No analysis jobs found")
    else:
        for record in response['records']:
            job_id = record[0]['stringValue']
            user_id = record[1]['stringValue']
            status = record[2]['stringValue']
            error = record[3].get('stringValue', 'None') if record[3].get('stringValue') else 'None'
            created = record[4]['stringValue']
            updated = record[5]['stringValue']

            print(f"\nJob ID: {job_id}")
            print(f"User: {user_id}")
            print(f"Status: {status}")
            print(f"Error: {error}")
            print(f"Created: {created}")
            print(f"Updated: {updated}")
            print("-" * 100)

except Exception as e:
    print(f"❌ Error querying database: {e}")
    import traceback
    traceback.print_exc()
