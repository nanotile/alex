#!/usr/bin/env python3
"""Check what tables exist in the database"""

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

# Query to list all tables
sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name
"""

try:
    response = rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=sql
    )

    print("📋 Tables in database:")
    print("=" * 60)

    if not response.get('records'):
        print("⚠️  No tables found in the database!")
        print("\nYou may need to run the database schema setup script.")
    else:
        for record in response['records']:
            table_name = record[0]['stringValue']
            print(f"  - {table_name}")

        print(f"\nTotal tables: {len(response['records'])}")

except Exception as e:
    print(f"❌ Error querying database: {e}")
    import traceback
    traceback.print_exc()
