

#!/usr/bin/env python3
"""
Full test for Reporter agent via Lambda - with portfolio data handling
"""

import os
import json
import boto3
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database
from src.schemas import JobCreate

def log_with_timestamp(message):
    """Helper to log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")

def test_reporter_lambda():
    """Test the Reporter agent via Lambda invocation"""
    
    start_time = time.time()
    log_with_timestamp("=== Starting Reporter Lambda Test ===")
    
    # Initialize database
    log_with_timestamp("Initializing database connection...")
    try:
        db = Database()
        log_with_timestamp(f"✓ Database initialized ({time.time() - start_time:.2f}s)")
        log_with_timestamp(f"Database client type: {type(db.client).__name__}")
    except Exception as e:
        log_with_timestamp(f"✗ Database initialization failed: {e}")
        import traceback
        log_with_timestamp(f"Traceback:\n{traceback.format_exc()}")
        return
    
    # Check for test user and portfolio data
    test_user_id = "test_user_001"
    log_with_timestamp(f"\nChecking test user: {test_user_id}")
    
    try:
        user = db.users.find_by_clerk_id(test_user_id)
        if not user:
            log_with_timestamp(f"✗ Test user not found!")
            log_with_timestamp("Please create test user first:")
            log_with_timestamp("  cd ../database && uv run reset_db.py --with-test-data")
            return
        
        log_with_timestamp(f"✓ User found: {user.get('display_name', test_user_id)}")
        log_with_timestamp(f"  User ID: {user.get('id')}")
        
    except Exception as e:
        log_with_timestamp(f"✗ Error finding user: {e}")
        return
    
    # Check portfolio data
    log_with_timestamp("\nChecking portfolio data...")
    try:
        accounts = db.accounts.find_by_user(test_user_id)
        log_with_timestamp(f"Found {len(accounts)} accounts")
        
        portfolio_data = {
            'user': user,
            'accounts': [],
            'total_positions': 0,
            'total_value': 0
        }
        
        for account in accounts:
            log_with_timestamp(f"\n  Account: {account.get('account_name', 'Unnamed')}")
            log_with_timestamp(f"    Type: {account.get('account_type', 'N/A')}")
            
            # Handle balance formatting
            try:
                balance = float(account.get('balance', 0))
                log_with_timestamp(f"    Balance: ${balance:,.2f}")
            except (ValueError, TypeError):
                log_with_timestamp(f"    Balance: ${account.get('balance', 'N/A')}")
            
            # Get positions
            positions = db.positions.find_by_account(account['id'])
            log_with_timestamp(f"    Positions: {len(positions)}")
            
            account_data = {
                'account': account,
                'positions': positions
            }
            portfolio_data['accounts'].append(account_data)
            portfolio_data['total_positions'] += len(positions)
            
            # Show position details
            for pos in positions[:3]:  # Show first 3 positions
                try:
                    shares = float(pos.get('shares', 0))
                    price = float(pos.get('current_price', 0))
                    log_with_timestamp(f"      - {pos.get('symbol', 'N/A')}: "
                                     f"{shares:.2f} shares @ ${price:.2f}")
                except (ValueError, TypeError):
                    log_with_timestamp(f"      - {pos.get('symbol', 'N/A')}: "
                                     f"{pos.get('shares', 'N/A')} shares @ ${pos.get('current_price', 'N/A')}")
            if len(positions) > 3:
                log_with_timestamp(f"      ... and {len(positions) - 3} more")
        
        log_with_timestamp(f"\n✓ Total accounts: {len(accounts)}")
        log_with_timestamp(f"✓ Total positions: {portfolio_data['total_positions']}")
        
        if len(accounts) == 0 or portfolio_data['total_positions'] == 0:
            log_with_timestamp("\n⚠️  WARNING: No portfolio data found!")
            log_with_timestamp("The reporter needs portfolio data to generate a report.")
            log_with_timestamp("Please run: cd ../database && uv run reset_db.py --with-test-data")
            return
            
    except Exception as e:
        log_with_timestamp(f"✗ Error checking portfolio: {e}")
        import traceback
        log_with_timestamp(f"Traceback:\n{traceback.format_exc()}")
        return
    
    # Initialize Lambda client
    log_with_timestamp("\nInitializing Lambda client...")
    try:
        lambda_client = boto3.client('lambda')
        log_with_timestamp(f"✓ Lambda client initialized ({time.time() - start_time:.2f}s)")
    except Exception as e:
        log_with_timestamp(f"✗ Lambda client initialization failed: {e}")
        return
    
    # Create test job with portfolio data
    log_with_timestamp(f"\nCreating test job for user: {test_user_id}")
    
    try:
        job_create = JobCreate(
            clerk_user_id=test_user_id,
            job_type="portfolio_analysis",
            request_payload={
                "analysis_type": "test",
                "test": True,
                "include_portfolio": True
            }
        )
        job_id = db.jobs.create(job_create.model_dump())
        log_with_timestamp(f"✓ Job created: {job_id} ({time.time() - start_time:.2f}s)")
    except Exception as e:
        log_with_timestamp(f"✗ Job creation failed: {e}")
        import traceback
        log_with_timestamp(f"Traceback:\n{traceback.format_exc()}")
        return
    
    print("=" * 60)
    
    # Prepare Lambda payload with portfolio data
    log_with_timestamp(f"\nPreparing Lambda payload...")
    
    # Option 1: Just pass job_id (Lambda should fetch portfolio data)
    lambda_payload_simple = {
        'job_id': job_id
    }
    
    # Option 2: Include portfolio data in payload
    lambda_payload_with_data = {
        'job_id': job_id,
        'clerk_user_id': test_user_id,
        'portfolio': {
            'accounts': [
                {
                    'account_name': acc['account'].get('account_name'),
                    'account_type': acc['account'].get('account_type'),
                    'balance': float(acc['account'].get('balance', 0)) if acc['account'].get('balance') else 0,
                    'positions': [
                        {
                            'symbol': pos.get('symbol'),
                            'shares': float(pos.get('shares', 0)) if pos.get('shares') else 0,
                            'current_price': float(pos.get('current_price', 0)) if pos.get('current_price') else 0,
                            'cost_basis': float(pos.get('cost_basis', 0)) if pos.get('cost_basis') else 0
                        }
                        for pos in acc['positions']
                    ]
                }
                for acc in portfolio_data['accounts']
            ]
        }
    }
    
    log_with_timestamp(f"Option 1 - Simple payload (job_id only): {json.dumps(lambda_payload_simple)}")
    log_with_timestamp(f"Option 2 - With portfolio data: {len(json.dumps(lambda_payload_with_data))} bytes")
    
    # Try with simple payload first
    log_with_timestamp(f"\n🔹 Attempt 1: Invoking with simple payload (job_id only)")
    invoke_start = time.time()
    try:
        response = lambda_client.invoke(
            FunctionName='alex-reporter',
            InvocationType='RequestResponse',
            Payload=json.dumps(lambda_payload_simple)
        )
        invoke_duration = time.time() - invoke_start
        log_with_timestamp(f"✓ Lambda invoked successfully (took {invoke_duration:.2f}s)")
        
        # Check response
        log_with_timestamp(f"Response StatusCode: {response.get('StatusCode')}")
        log_with_timestamp(f"Response FunctionError: {response.get('FunctionError', 'None')}")
        
        result = json.loads(response['Payload'].read())
        log_with_timestamp(f"Lambda Response: {json.dumps(result, indent=2)}")
        
        # If we got a 400 error, try with portfolio data
        if result.get('statusCode') == 400 and 'No portfolio data' in result.get('body', ''):
            log_with_timestamp(f"\n⚠️  Lambda expects portfolio data in payload")
            log_with_timestamp(f"🔹 Attempt 2: Invoking with portfolio data included")
            
            invoke_start = time.time()
            response = lambda_client.invoke(
                FunctionName='alex-reporter',
                InvocationType='RequestResponse',
                Payload=json.dumps(lambda_payload_with_data)
            )
            invoke_duration = time.time() - invoke_start
            log_with_timestamp(f"✓ Lambda invoked successfully (took {invoke_duration:.2f}s)")
            
            result = json.loads(response['Payload'].read())
            log_with_timestamp(f"Lambda Response: {json.dumps(result, indent=2)}")
        
        # Check for errors in response
        if 'errorMessage' in result:
            log_with_timestamp(f"⚠️  Lambda returned error: {result['errorMessage']}")
            if 'errorType' in result:
                log_with_timestamp(f"⚠️  Error type: {result['errorType']}")
            if 'stackTrace' in result:
                log_with_timestamp(f"⚠️  Stack trace:")
                for line in result['stackTrace']:
                    log_with_timestamp(f"    {line}")
            return
            
    except Exception as e:
        log_with_timestamp(f"✗ Error invoking Lambda (after {time.time() - invoke_start:.2f}s): {e}")
        log_with_timestamp(f"Exception type: {type(e).__name__}")
        import traceback
        log_with_timestamp(f"Traceback:\n{traceback.format_exc()}")
        return
    
    # Poll database for results
    log_with_timestamp("\nPolling database for job completion...")
    max_wait = 30  # Maximum 30 seconds
    poll_interval = 1  # Check every second
    poll_start = time.time()
    
    job = None
    while time.time() - poll_start < max_wait:
        try:
            job = db.jobs.find_by_id(job_id)
            
            if job:
                status = job.get('status', 'unknown')
                log_with_timestamp(f"Job status: {status} (elapsed: {time.time() - poll_start:.1f}s)")
                
                if job.get('report_payload'):
                    log_with_timestamp(f"✓ Report found! (total time: {time.time() - start_time:.2f}s)")
                    break
                elif status == 'failed':
                    log_with_timestamp(f"✗ Job failed: {job.get('error_message', 'No error message')}")
                    break
                elif status == 'completed':
                    log_with_timestamp("⚠️  Job marked completed but no report payload")
                    break
            else:
                log_with_timestamp(f"⚠️  Job not found in database")
                
        except Exception as e:
            log_with_timestamp(f"✗ Error checking job status: {e}")
            
        time.sleep(poll_interval)
    
    # Final results check
    log_with_timestamp("\n=== Final Results ===")
    if job:
        log_with_timestamp(f"Job ID: {job_id}")
        log_with_timestamp(f"Job Status: {job.get('status', 'unknown')}")
        log_with_timestamp(f"Created At: {job.get('created_at')}")
        log_with_timestamp(f"Updated At: {job.get('updated_at')}")
        
        if job.get('report_payload'):
            log_with_timestamp("\n✅ Report generated successfully!")
            report = job['report_payload']
            
            # Handle both string and dict report payloads
            if isinstance(report, str):
                log_with_timestamp(f"Report length: {len(report)} characters")
                log_with_timestamp(f"Report preview:\n{report[:500]}...")
            elif isinstance(report, dict):
                log_with_timestamp(f"Report structure: {list(report.keys())}")
                if 'analysis' in report:
                    analysis = report['analysis']
                    log_with_timestamp(f"Analysis length: {len(analysis)} characters")
                    log_with_timestamp(f"Analysis preview:\n{analysis[:500]}...")
        else:
            log_with_timestamp("\n❌ No report found in database")
            if job.get('error_message'):
                log_with_timestamp(f"Error message: {job['error_message']}")
    else:
        log_with_timestamp("❌ Job not found in final check")
    
    total_time = time.time() - start_time
    log_with_timestamp(f"\nTotal execution time: {total_time:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    test_reporter_lambda()