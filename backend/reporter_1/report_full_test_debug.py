#!/usr/bin/env python3
"""
Full test for Reporter agent via Lambda
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
    log_with_timestamp("Checking database environment variables...")
    
    # Check all database-related environment variables
    db_env_vars = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'MONGO_URI': os.getenv('MONGO_URI'),
        'MONGODB_URI': os.getenv('MONGODB_URI'),
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_NAME': os.getenv('DB_NAME'),
        'DB_USER': os.getenv('DB_USER'),
        'AWS_REGION': os.getenv('AWS_REGION'),
        'DYNAMODB_TABLE': os.getenv('DYNAMODB_TABLE'),
    }
    
    for key, value in db_env_vars.items():
        if value:
            # Mask sensitive parts of connection strings
            if 'URI' in key or 'URL' in key:
                if '@' in value:
                    # Mask credentials in connection string
                    masked = value.split('@')[0].split('://')
                    if len(masked) > 1:
                        protocol = masked[0] + '://'
                        host_part = value.split('@')[1] if '@' in value else '***'
                        log_with_timestamp(f"  {key}: {protocol}***:***@{host_part}")
                    else:
                        log_with_timestamp(f"  {key}: {value[:20]}...{value[-20:]}")
                else:
                    log_with_timestamp(f"  {key}: {value}")
            elif 'PASSWORD' in key or 'SECRET' in key:
                log_with_timestamp(f"  {key}: ***masked***")
            else:
                log_with_timestamp(f"  {key}: {value}")
        else:
            log_with_timestamp(f"  {key}: (not set)")
    
    # Check current working directory
    log_with_timestamp(f"Current working directory: {os.getcwd()}")
    
    # Check if src module exists
    try:
        import src
        log_with_timestamp(f"src module location: {src.__file__}")
    except Exception as e:
        log_with_timestamp(f"Warning: Could not import src module: {e}")
    
    try:
        db = Database()
        log_with_timestamp(f"✓ Database initialized ({time.time() - start_time:.2f}s)")
        
        # Try to get database type/info
        try:
            if hasattr(db, 'client'):
                log_with_timestamp(f"Database client type: {type(db.client).__name__}")
            if hasattr(db, 'db'):
                log_with_timestamp(f"Database object type: {type(db.db).__name__}")
                if hasattr(db.db, 'name'):
                    log_with_timestamp(f"Database name: {db.db.name}")
            if hasattr(db, '_db_path'):
                log_with_timestamp(f"Database path: {db._db_path}")
            
            # Try to list collections/tables
            try:
                if hasattr(db, 'db'):
                    if hasattr(db.db, 'list_collection_names'):
                        collections = db.db.list_collection_names()
                        log_with_timestamp(f"Available collections: {collections}")
                    elif hasattr(db.db, 'list_tables'):
                        tables = db.db.list_tables()
                        log_with_timestamp(f"Available tables: {tables}")
            except Exception as e:
                log_with_timestamp(f"Note: Could not list collections/tables: {e}")
                
        except Exception as e:
            log_with_timestamp(f"Note: Could not get database details: {e}")
            
    except Exception as e:
        log_with_timestamp(f"✗ Database initialization failed: {e}")
        log_with_timestamp(f"Exception type: {type(e).__name__}")
        
        # Show full traceback
        import traceback
        log_with_timestamp(f"Full traceback:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                log_with_timestamp(f"  {line}")
        
        # Try to show what the Database class is trying to do
        try:
            import inspect
            log_with_timestamp("\nDatabase class initialization signature:")
            log_with_timestamp(f"  {inspect.signature(Database.__init__)}")
            
            # Show Database class source file
            log_with_timestamp(f"Database class defined in: {inspect.getfile(Database)}")
            
            # Try to show the __init__ method source
            try:
                source_lines = inspect.getsource(Database.__init__)
                log_with_timestamp("\nDatabase.__init__ source code:")
                for line in source_lines.split('\n')[:20]:  # First 20 lines
                    log_with_timestamp(f"  {line}")
            except Exception as e3:
                log_with_timestamp(f"Could not get __init__ source: {e3}")
                
        except Exception as e2:
            log_with_timestamp(f"Could not inspect Database class: {e2}")
        
        # Check if .env file exists and show its location
        log_with_timestamp("\n.env file check:")
        env_paths = ['.env', '../.env', '../../.env']
        for env_path in env_paths:
            abs_path = os.path.abspath(env_path)
            exists = os.path.exists(abs_path)
            log_with_timestamp(f"  {abs_path}: {'EXISTS' if exists else 'not found'}")
        
        return
    
    # Initialize Lambda client
    log_with_timestamp("Initializing Lambda client...")
    try:
        lambda_client = boto3.client('lambda')
        log_with_timestamp(f"✓ Lambda client initialized ({time.time() - start_time:.2f}s)")
    except Exception as e:
        log_with_timestamp(f"✗ Lambda client initialization failed: {e}")
        return
    
    # Create test job
    test_user_id = "test_user_001"
    log_with_timestamp(f"Creating test job for user: {test_user_id}")
    
    try:
        job_create = JobCreate(
            clerk_user_id=test_user_id,
            job_type="portfolio_analysis",
            request_payload={"analysis_type": "test", "test": True}
        )
        job_id = db.jobs.create(job_create.model_dump())
        log_with_timestamp(f"✓ Job created: {job_id} ({time.time() - start_time:.2f}s)")
    except Exception as e:
        log_with_timestamp(f"✗ Job creation failed: {e}")
        import traceback
        log_with_timestamp(f"Traceback:\n{traceback.format_exc()}")
        return
    
    print("=" * 60)
    
    # Invoke Lambda
    log_with_timestamp(f"Invoking Lambda function: alex-reporter")
    log_with_timestamp(f"Payload: {{'job_id': '{job_id}'}}")
    
    invoke_start = time.time()
    try:
        response = lambda_client.invoke(
            FunctionName='alex-reporter',
            InvocationType='RequestResponse',
            Payload=json.dumps({'job_id': job_id})
        )
        invoke_duration = time.time() - invoke_start
        log_with_timestamp(f"✓ Lambda invoked successfully (took {invoke_duration:.2f}s)")
        
        # Check response metadata
        log_with_timestamp(f"Response StatusCode: {response.get('StatusCode')}")
        log_with_timestamp(f"Response FunctionError: {response.get('FunctionError', 'None')}")
        
        if 'LogResult' in response:
            log_with_timestamp(f"Lambda execution logs available")
        
        # Read payload
        log_with_timestamp("Reading Lambda response payload...")
        payload_read_start = time.time()
        result = json.loads(response['Payload'].read())
        log_with_timestamp(f"✓ Payload read (took {time.time() - payload_read_start:.2f}s)")
        log_with_timestamp(f"Lambda Response: {json.dumps(result, indent=2)}")
        
        # Check for errors in response
        if 'errorMessage' in result:
            log_with_timestamp(f"⚠️  Lambda returned error: {result['errorMessage']}")
        if 'errorType' in result:
            log_with_timestamp(f"⚠️  Error type: {result['errorType']}")
            
    except lambda_client.exceptions.RequestTooLarge as e:
        log_with_timestamp(f"✗ Request too large: {e}")
        return
    except lambda_client.exceptions.ResourceNotFoundException as e:
        log_with_timestamp(f"✗ Lambda function not found: {e}")
        return
    except lambda_client.exceptions.ServiceException as e:
        log_with_timestamp(f"✗ Lambda service error: {e}")
        return
    except Exception as e:
        log_with_timestamp(f"✗ Error invoking Lambda (after {time.time() - invoke_start:.2f}s): {e}")
        log_with_timestamp(f"Exception type: {type(e).__name__}")
        import traceback
        log_with_timestamp(f"Traceback:\n{traceback.format_exc()}")
        return
    
    # Poll database for results
    log_with_timestamp("Polling database for job completion...")
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
            log_with_timestamp(f"Report length: {len(report)} characters")
            log_with_timestamp(f"Report preview:\n{report[:500]}...")
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