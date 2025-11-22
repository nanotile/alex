#!/usr/bin/env python3
"""
Direct database inspection - bypassing ORM to see raw data
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database

def main():
    print("=" * 70)
    print("🔍 Direct Database Inspection")
    print("=" * 70)
    
    db = Database()
    
    # Direct SQL query to see positions
    print("\n1. RAW POSITIONS TABLE")
    print("-" * 70)
    
    try:
        # Try to execute raw SQL if possible
        if hasattr(db, 'client') and hasattr(db.client, 'execute_statement'):
            # Using AWS RDS Data API
            response = db.client.execute_statement(
                resourceArn=os.getenv('DB_RESOURCE_ARN'),
                secretArn=os.getenv('DB_SECRET_ARN'),
                database=os.getenv('DB_NAME', 'alex'),
                sql="SELECT * FROM positions ORDER BY created_at DESC LIMIT 10"
            )
            
            print("Raw query response:")
            import json
            print(json.dumps(response, indent=2, default=str))
            
            if 'records' in response:
                print(f"\nFound {len(response['records'])} positions")
                for i, record in enumerate(response['records'], 1):
                    print(f"\nPosition {i}:")
                    for j, col in enumerate(record):
                        print(f"  Column {j}: {col}")
        else:
            print("Cannot execute raw SQL with this database client")
            
    except Exception as e:
        print(f"Error executing raw SQL: {e}")
        import traceback
        print(traceback.format_exc())
    
    # Use ORM but show field mappings
    print("\n2. ORM QUERY RESULTS")
    print("-" * 70)
    
    test_user_id = "test_user_001"
    accounts = db.accounts.find_by_user(test_user_id)
    
    if accounts:
        account_id = accounts[0]['id']
        print(f"Querying positions for account: {account_id}")
        
        positions = db.positions.find_by_account(account_id)
        print(f"Found {len(positions)} positions")
        
        for i, pos in enumerate(positions, 1):
            print(f"\nPosition {i}:")
            print(f"  Type: {type(pos)}")
            print(f"  Keys: {list(pos.keys()) if hasattr(pos, 'keys') else 'N/A'}")
            print(f"  Full object: {pos}")
            
            # Try to access shares in different ways
            print(f"\n  Accessing 'shares' field:")
            print(f"    pos['shares'] = {pos.get('shares', 'KEY NOT FOUND')}")
            print(f"    pos.get('shares') = {pos.get('shares', 'DEFAULT')}")
            
            if 'shares' in pos:
                shares_value = pos['shares']
                print(f"    Type: {type(shares_value)}")
                print(f"    Value: {shares_value}")
                print(f"    Repr: {repr(shares_value)}")
    
    # Check database schema
    print("\n3. DATABASE SCHEMA")
    print("-" * 70)
    
    try:
        if hasattr(db, 'client') and hasattr(db.client, 'execute_statement'):
            response = db.client.execute_statement(
                resourceArn=os.getenv('DB_RESOURCE_ARN'),
                secretArn=os.getenv('DB_SECRET_ARN'),
                database=os.getenv('DB_NAME', 'alex'),
                sql="""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'positions'
                ORDER BY ordinal_position
                """
            )
            
            print("Positions table schema:")
            import json
            print(json.dumps(response, indent=2, default=str))
    except Exception as e:
        print(f"Could not get schema: {e}")
    
    # Check if there's a field mapping issue
    print("\n4. POSITIONS CLASS INSPECTION")
    print("-" * 70)
    
    try:
        import inspect
        positions_class = db.positions.__class__
        print(f"Positions class: {positions_class}")
        print(f"Methods: {[m for m in dir(db.positions) if not m.startswith('_')]}")
        
        # Check if there's a field mapping
        if hasattr(db.positions, '_fields'):
            print(f"Field mapping: {db.positions._fields}")
        if hasattr(db.positions, 'model_fields'):
            print(f"Model fields: {db.positions.model_fields}")
            
    except Exception as e:
        print(f"Could not inspect positions class: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()