#!/usr/bin/env python3
"""Watch analysis progress in real-time"""

import boto3
import os
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(override=True)

# Get environment variables
cluster_arn = os.getenv('AURORA_CLUSTER_ARN')
secret_arn = os.getenv('AURORA_SECRET_ARN')
database_name = os.getenv('AURORA_DATABASE_NAME', 'alex')
region = os.getenv('DEFAULT_AWS_REGION', 'us-east-1')

# Create RDS Data client
rds_data = boto3.client('rds-data', region_name=region)

def get_latest_job():
    sql = """
        SELECT
            id,
            status,
            created_at,
            started_at,
            completed_at
        FROM jobs
        ORDER BY created_at DESC
        LIMIT 1
    """

    response = rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=sql
    )

    if response.get('records'):
        record = response['records'][0]
        return {
            'id': record[0]['stringValue'],
            'status': record[1]['stringValue'],
            'created_at': record[2]['stringValue'],
            'started_at': record[3].get('stringValue') if record[3].get('stringValue') else None,
            'completed_at': record[4].get('stringValue') if record[4].get('stringValue') else None
        }
    return None

def calculate_elapsed(start_str, end_str=None):
    """Calculate elapsed time in seconds"""
    if not start_str:
        return 0

    start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))

    if end_str:
        end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
    else:
        end = datetime.now(start.tzinfo)

    return (end - start).total_seconds()

print("\n" + "="*80)
print("📊 WATCHING ANALYSIS PROGRESS")
print("="*80)
print("\nPress Ctrl+C to stop\n")

last_status = None
start_time = None

try:
    while True:
        job = get_latest_job()

        if job:
            if last_status != job['status']:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Job {job['id'][:8]}...")
                print(f"  Status: {job['status']}")

                if job['started_at']:
                    elapsed = calculate_elapsed(job['created_at'], job['started_at'])
                    print(f"  Queue time: {elapsed:.1f}s")

                if job['status'] == 'running' and job['started_at']:
                    if not start_time:
                        start_time = job['started_at']

                if job['status'] == 'completed' and job['completed_at']:
                    total_time = calculate_elapsed(job['started_at'], job['completed_at'])
                    queue_time = calculate_elapsed(job['created_at'], job['started_at'])
                    print(f"  Execution time: {total_time:.1f}s")
                    print(f"  Total time: {total_time + queue_time:.1f}s")
                    print("\n✅ Analysis complete!")
                    break

                last_status = job['status']

            elif job['status'] == 'running' and start_time:
                elapsed = calculate_elapsed(start_time)
                print(f"\r  Running for {elapsed:.0f}s...", end='', flush=True)

        time.sleep(2)

except KeyboardInterrupt:
    print("\n\nStopped watching.")
