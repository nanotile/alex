#!/usr/bin/env python3
"""
Run a full end-to-end test of the Alex agent orchestration.
This creates a test job and monitors it through completion.

Usage:
    cd backend/planner
    uv run run_full_test.py
"""

import os
import json
import boto3
import time
import logging
import traceback
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import database
from src import Database

# Get configuration
QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'alex-analysis-jobs')


def log_with_timestamp(message, level="INFO"):
    """Helper to log messages with timestamp and elapsed time."""
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)


def get_queue_url(sqs):
    """Get the SQS queue URL."""
    try:
        log_with_timestamp(f"Looking for SQS queue: {QUEUE_NAME}")
        response = sqs.list_queues(QueueNamePrefix=QUEUE_NAME)
        queues = response.get('QueueUrls', [])
        
        log_with_timestamp(f"Found {len(queues)} queues matching prefix")
        for queue_url in queues:
            log_with_timestamp(f"  - {queue_url}")
            if QUEUE_NAME in queue_url:
                log_with_timestamp(f"✓ Matched queue URL: {queue_url}")
                return queue_url
        
        raise ValueError(f"Queue {QUEUE_NAME} not found")
    except Exception as e:
        log_with_timestamp(f"Error getting queue URL: {e}", "ERROR")
        raise


def check_queue_status(sqs, queue_url):
    """Check the queue attributes to diagnose issues."""
    try:
        log_with_timestamp("Checking SQS queue attributes...")
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        attrs = response.get('Attributes', {})
        
        log_with_timestamp(f"Queue attributes:")
        log_with_timestamp(f"  - Messages available: {attrs.get('ApproximateNumberOfMessages', 0)}")
        log_with_timestamp(f"  - Messages in flight: {attrs.get('ApproximateNumberOfMessagesNotVisible', 0)}")
        log_with_timestamp(f"  - Messages delayed: {attrs.get('ApproximateNumberOfMessagesDelayed', 0)}")
        log_with_timestamp(f"  - Visibility timeout: {attrs.get('VisibilityTimeout', 'N/A')}s")
        log_with_timestamp(f"  - Message retention: {attrs.get('MessageRetentionPeriod', 'N/A')}s")
        
        return attrs
    except Exception as e:
        log_with_timestamp(f"Error checking queue status: {e}", "WARNING")
        return {}


def verify_database_connection(db):
    """Verify database connectivity."""
    try:
        log_with_timestamp("Verifying database connection...")
        # Try a simple query
        test_user = db.users.find_by_clerk_id('test_user_001')
        log_with_timestamp("✓ Database connection successful")
        return True
    except Exception as e:
        log_with_timestamp(f"✗ Database connection failed: {e}", "ERROR")
        log_with_timestamp(traceback.format_exc(), "ERROR")
        return False


def main():
    """Run the full test."""
    start_time = time.time()
    
    print("=" * 70)
    print("🎯 Alex Agent Orchestration - Full Test (Debug Mode)")
    print("=" * 70)
    
    # Initialize AWS clients
    log_with_timestamp("Initializing AWS clients...")
    try:
        sqs = boto3.client('sqs')
        sts = boto3.client('sts')
        log_with_timestamp(f"✓ AWS clients initialized ({time.time() - start_time:.2f}s)")
    except Exception as e:
        log_with_timestamp(f"✗ Failed to initialize AWS clients: {e}", "ERROR")
        return 1
    
    # Display AWS info
    try:
        account_id = sts.get_caller_identity()['Account']
        region = boto3.Session().region_name
        log_with_timestamp(f"AWS Account: {account_id}")
        log_with_timestamp(f"AWS Region: {region}")
        log_with_timestamp(f"Bedrock Region: {os.getenv('BEDROCK_REGION', 'us-west-2')}")
        log_with_timestamp(f"Bedrock Model: {os.getenv('BEDROCK_MODEL_ID', 'Not set')}")
    except Exception as e:
        log_with_timestamp(f"Warning: Could not get AWS info: {e}", "WARNING")
    
    print()
    
    # Initialize database
    log_with_timestamp("Initializing database...")
    try:
        db = Database()
        log_with_timestamp(f"✓ Database object created ({time.time() - start_time:.2f}s)")
        
        if not verify_database_connection(db):
            return 1
            
    except Exception as e:
        log_with_timestamp(f"✗ Failed to initialize database: {e}", "ERROR")
        log_with_timestamp(traceback.format_exc(), "ERROR")
        return 1
    
    # Check for test user
    log_with_timestamp("Checking test data...")
    test_user_id = 'test_user_001'
    
    try:
        user = db.users.find_by_clerk_id(test_user_id)
        
        if not user:
            log_with_timestamp("❌ Test user not found", "ERROR")
            print("\nPlease run database setup first:")
            print("   cd ../database && uv run reset_db.py --with-test-data")
            return 1
        
        log_with_timestamp(f"✓ Test user: {user.get('display_name', test_user_id)}")
    except Exception as e:
        log_with_timestamp(f"✗ Error checking test user: {e}", "ERROR")
        return 1
    
    # Check accounts and positions
    try:
        log_with_timestamp("Checking portfolio data...")
        accounts = db.accounts.find_by_user(test_user_id)
        total_positions = 0
        for account in accounts:
            positions = db.positions.find_by_account(account['id'])
            total_positions += len(positions)
        
        log_with_timestamp(f"✓ Portfolio: {len(accounts)} accounts, {total_positions} positions")
    except Exception as e:
        log_with_timestamp(f"Warning: Error checking portfolio: {e}", "WARNING")
    
    # Create test job
    log_with_timestamp("\n🚀 Creating test job...")
    job_data = {
        'clerk_user_id': test_user_id,
        'job_type': 'portfolio_analysis',
        'status': 'pending',
        'request_payload': {
            'analysis_type': 'full',
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'test_run': True,
            'debug_mode': True
        }
    }
    
    try:
        job_id = db.jobs.create(job_data)
        log_with_timestamp(f"✓ Created job: {job_id} ({time.time() - start_time:.2f}s)")
        
        # Verify job was created
        job_check = db.jobs.find_by_id(job_id)
        if job_check:
            log_with_timestamp(f"✓ Job verified in database: status={job_check.get('status')}")
        else:
            log_with_timestamp("⚠️  Job not found immediately after creation", "WARNING")
    except Exception as e:
        log_with_timestamp(f"✗ Failed to create job: {e}", "ERROR")
        log_with_timestamp(traceback.format_exc(), "ERROR")
        return 1
    
    # Get SQS queue
    log_with_timestamp("\n📤 Preparing to send job to SQS...")
    try:
        queue_url = get_queue_url(sqs)
        
        # Check queue status before sending
        check_queue_status(sqs, queue_url)
        
    except Exception as e:
        log_with_timestamp(f"✗ Failed to get queue URL: {e}", "ERROR")
        return 1
    
    # Send to SQS
    log_with_timestamp(f"Sending message to queue: {queue_url}")
    message_body = json.dumps({'job_id': job_id})
    log_with_timestamp(f"Message body: {message_body}")
    
    try:
        send_start = time.time()
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
        send_duration = time.time() - send_start
        
        log_with_timestamp(f"✓ Message sent in {send_duration:.2f}s")
        log_with_timestamp(f"  - Message ID: {response['MessageId']}")
        log_with_timestamp(f"  - MD5 of body: {response.get('MD5OfMessageBody', 'N/A')}")
        
        # Check queue status after sending
        check_queue_status(sqs, queue_url)
        
    except Exception as e:
        log_with_timestamp(f"✗ Failed to send to SQS: {e}", "ERROR")
        log_with_timestamp(traceback.format_exc(), "ERROR")
        return 1
    
    # Monitor job
    log_with_timestamp("\n⏳ Monitoring job progress (timeout: 3 minutes)...")
    print("-" * 50)
    
    monitor_start = time.time()
    timeout = 180  # 3 minutes
    last_status = None
    status_changes = []
    poll_count = 0
    
    while time.time() - monitor_start < timeout:
        poll_count += 1
        try:
            job = db.jobs.find_by_id(job_id)
            
            if not job:
                log_with_timestamp(f"⚠️  Job not found in database (poll #{poll_count})", "WARNING")
                time.sleep(2)
                continue
            
            status = job['status']
            elapsed = int(time.time() - monitor_start)
            
            if status != last_status:
                log_with_timestamp(f"[{elapsed:3d}s] Status changed: {last_status} → {status}")
                status_changes.append({
                    'from': last_status,
                    'to': status,
                    'elapsed': elapsed,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                last_status = status
                
                # Log additional details on status change
                if status == 'processing':
                    log_with_timestamp(f"  Job processing started")
                elif status == 'completed':
                    log_with_timestamp(f"  Job completed!")
                    # Check what payloads are present
                    payloads = []
                    if job.get('summary_payload'):
                        payloads.append('summary')
                    if job.get('report_payload'):
                        payloads.append('report')
                    if job.get('charts_payload'):
                        payloads.append('charts')
                    if job.get('retirement_payload'):
                        payloads.append('retirement')
                    log_with_timestamp(f"  Payloads present: {', '.join(payloads) if payloads else 'none'}")
                elif status == 'failed':
                    log_with_timestamp(f"  Job failed!", "ERROR")
                    if job.get('error_message'):
                        log_with_timestamp(f"  Error: {job['error_message']}", "ERROR")
            
            # Periodic status update even if status hasn't changed
            if poll_count % 15 == 0:  # Every 30 seconds (15 polls * 2s)
                log_with_timestamp(f"[{elapsed:3d}s] Still {status}... (poll #{poll_count})")
            
            if status == 'completed':
                print("-" * 50)
                log_with_timestamp("✅ Job completed successfully!")
                break
            elif status == 'failed':
                print("-" * 50)
                log_with_timestamp(f"❌ Job failed: {job.get('error_message', 'Unknown error')}", "ERROR")
                
                # Log status change history
                log_with_timestamp("\nStatus change history:")
                for change in status_changes:
                    log_with_timestamp(f"  [{change['elapsed']}s] {change['from']} → {change['to']}")
                
                return 1
            
            time.sleep(2)
            
        except Exception as e:
            log_with_timestamp(f"Error polling job status (poll #{poll_count}): {e}", "ERROR")
            log_with_timestamp(traceback.format_exc(), "ERROR")
            time.sleep(2)
    else:
        print("-" * 50)
        log_with_timestamp(f"❌ Job timed out after {timeout}s", "ERROR")
        log_with_timestamp(f"Total polls: {poll_count}")
        log_with_timestamp(f"Final status: {last_status}")
        
        # Log status change history
        log_with_timestamp("\nStatus change history:")
        for change in status_changes:
            log_with_timestamp(f"  [{change['elapsed']}s] {change['from']} → {change['to']}")
        
        return 1
    
    # Display results
    print("\n" + "=" * 70)
    print("📋 ANALYSIS RESULTS")
    print("=" * 70)
    
    try:
        # Orchestrator summary
        if job.get('summary_payload'):
            log_with_timestamp("\n🎯 Orchestrator Summary:")
            summary = job['summary_payload']
            log_with_timestamp(f"Summary: {summary.get('summary', 'N/A')}")
            
            if summary.get('key_findings'):
                log_with_timestamp("\nKey Findings:")
                for finding in summary['key_findings']:
                    log_with_timestamp(f"  • {finding}")
            
            if summary.get('recommendations'):
                log_with_timestamp("\nRecommendations:")
                for rec in summary['recommendations']:
                    log_with_timestamp(f"  • {rec}")
        else:
            log_with_timestamp("⚠️  No orchestrator summary found", "WARNING")
        
        # Report analysis
        if job.get('report_payload'):
            log_with_timestamp("\n📝 Portfolio Report:")
            report = job['report_payload']
            analysis = report.get('analysis', '')
            log_with_timestamp(f"  Length: {len(analysis)} characters")
            if analysis:
                preview = analysis[:300]
                if len(analysis) > 300:
                    preview += "..."
                log_with_timestamp(f"  Preview: {preview}")
        else:
            log_with_timestamp("⚠️  No portfolio report found", "WARNING")
        
        # Charts
        if job.get('charts_payload'):
            log_with_timestamp(f"\n📊 Visualizations: {len(job['charts_payload'])} charts")
            for chart_key, chart_data in job['charts_payload'].items():
                log_with_timestamp(f"  • {chart_key}: {chart_data.get('title', 'Untitled')}")
                if chart_data.get('data'):
                    log_with_timestamp(f"    Data points: {len(chart_data['data'])}")
        else:
            log_with_timestamp("⚠️  No charts found", "WARNING")
        
        # Retirement projections
        if job.get('retirement_payload'):
            log_with_timestamp("\n🎯 Retirement Analysis:")
            ret = job['retirement_payload']
            log_with_timestamp(f"  Success Rate: {ret.get('success_rate', 'N/A')}%")
            log_with_timestamp(f"  Projected Value: ${ret.get('projected_value', 0):,.0f}")
            log_with_timestamp(f"  Years to Retirement: {ret.get('years_to_retirement', 'N/A')}")
        else:
            log_with_timestamp("⚠️  No retirement analysis found", "WARNING")
    
    except Exception as e:
        log_with_timestamp(f"Error displaying results: {e}", "ERROR")
        log_with_timestamp(traceback.format_exc(), "ERROR")
    
    # Final timing summary
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("⏱️  TIMING SUMMARY")
    print("=" * 70)
    log_with_timestamp(f"Total execution time: {total_time:.2f}s")
    log_with_timestamp(f"Status changes: {len(status_changes)}")
    log_with_timestamp(f"Total polls: {poll_count}")
    
    if status_changes:
        log_with_timestamp("\nStatus transition timeline:")
        for i, change in enumerate(status_changes):
            log_with_timestamp(f"  {i+1}. [{change['elapsed']}s] {change['from']} → {change['to']}")
    
    print("\n" + "=" * 70)
    print("✅ Full test completed successfully!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())