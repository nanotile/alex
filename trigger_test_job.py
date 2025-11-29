#!/usr/bin/env python3
"""
Trigger a test portfolio analysis job directly via SQS.
"""

import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

sqs = boto3.client('sqs', region_name='us-east-1')
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/393470797331/alex-analysis-jobs"

# Send message to SQS - the planner will pull the actual job from the database
message = {
    "job_id": "d58b197b-c2a1-4747-8610-81bd0cf26c99"  # Use existing job ID from logs
}

print(f"Sending message to SQS: {message}")
response = sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=json.dumps(message)
)

print(f"✅ Message sent successfully!")
print(f"   Message ID: {response['MessageId']}")
print(f"\n📊 Monitor execution:")
print(f"   aws logs tail /aws/lambda/alex-planner --follow")
