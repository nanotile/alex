#!/usr/bin/env python3
"""
Simple test to trigger a portfolio analysis and check for timing data.
"""

import os
import json
import boto3
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

sqs = boto3.client('sqs')
sts = boto3.client('sts')

# Get configuration
QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'alex-analysis-jobs')


def get_queue_url():
    """Get the SQS queue URL."""
    response = sqs.list_queues(QueueNamePrefix=QUEUE_NAME)
    queues = response.get('QueueUrls', [])

    for queue_url in queues:
        if QUEUE_NAME in queue_url:
            return queue_url

    raise ValueError(f"Queue {QUEUE_NAME} not found")


def main():
    """Run a simple timing test."""
    print("=" * 70)
    print("🎯 Testing Execution Timing Feature")
    print("=" * 70)

    # Display AWS info
    account_id = sts.get_caller_identity()['Account']
    region = boto3.Session().region_name
    print(f"AWS Account: {account_id}")
    print(f"AWS Region: {region}")
    print()

    # Use a test job ID
    job_id = f"test_timing_{int(time.time())}"

    # Send to SQS
    print(f"📤 Sending test job to SQS: {job_id}")
    try:
        queue_url = get_queue_url()
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                'job_id': job_id,
                'clerk_user_id': 'test_user_001',
                'test_run': True
            })
        )
        print(f"✓ Message sent: {response['MessageId']}")
        print()
        print("⏳ Job will be processed by Planner Lambda...")
        print("   Check CloudWatch logs for timing data:")
        print("   aws logs tail /aws/lambda/alex-planner --follow")
        print()
        print("✅ Test message sent successfully!")

    except Exception as e:
        print(f"❌ Failed to send to SQS: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
