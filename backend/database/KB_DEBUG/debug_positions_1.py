#!/usr/bin/env python3
"""
Debug position-account relationships
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database

def main():
    print("=" * 70)
    print("🔍 Position-Account Relationship Debug")
    print("=" * 70)
    
    db = Database()
    test_user_id = "test_user_001"
    
    # Get all accounts
    print("\n1. ALL ACCOUNTS")
    print("-" * 70)
    accounts = db.accounts.find_by_user(test_user_id)
    print(f"Found {len(accounts)} accounts\n")
    
    for i, acc in enumerate(accounts, 1):
        print(f"Account {i}:")
        print(f"  ID: {acc.get('id')}")
        print(f"  Name: {acc.get('account_name')}")
        print(f"  Clerk User ID: {acc.get('clerk_user_id')}")
        print()
    
    # Get ALL positions (not filtered by account)
    print("\n2. ALL POSITIONS IN DATABASE")
    print("-" * 70)
    
    all_positions = db.positions.find_all()
    print(f"Found {len(all_positions)} total positions\n")
    
    for i, pos in enumerate(all_positions, 1):
        print(f"Position {i}:")
        print(f"  ID: {pos.get('id')}")
        print(f"  Symbol: {pos.get('symbol')}")
        print(f"  Shares: {pos.get('shares')}")
        print(f"  Account ID: {pos.get('account_id')}")
        print(f"  All keys: {list(pos.keys())}")
        print()
    
    # Compare account IDs
    print("\n3. MATCHING ANALYSIS")
    print("-" * 70)
    
    account_ids = {acc['id']: acc['account_name'] for acc in accounts}
    position_account_ids = [pos.get('account_id') for pos in all_positions]
    
    print(f"Account IDs we have: {list(account_ids.keys())}")
    print(f"Position account_ids: {position_account_ids}")
    print()
    
    # Check for mismatches
    for pos_acc_id in position_account_ids:
        if pos_acc_id in account_ids:
            print(f"✓ Position account_id {pos_acc_id} matches account: {account_ids[pos_acc_id]}")
        else:
            print(f"✗ Position account_id {pos_acc_id} NOT FOUND in accounts!")
    
    print()
    for acc_id, acc_name in account_ids.items():
        matching_positions = [p for p in all_positions if p.get('account_id') == acc_id]
        print(f"Account '{acc_name}' ({acc_id}): {len(matching_positions)} positions")
    
    # Test the find_by_account method directly
    print("\n4. TESTING find_by_account METHOD")
    print("-" * 70)
    
    for acc in accounts:
        acc_id = acc['id']
        acc_name = acc['account_name']
        positions = db.positions.find_by_account(acc_id)
        print(f"find_by_account('{acc_id}')")
        print(f"  Account: {acc_name}")
        print(f"  Returned: {len(positions)} positions")
        if positions:
            for pos in positions:
                print(f"    - {pos.get('symbol')}: {pos.get('shares')} shares")
        print()
    
    # Check the positions table directly via the base query
    print("\n5. DIRECT TABLE CHECK")
    print("-" * 70)
    
    # Try to see if there's a filter or where clause issue
    import inspect
    if hasattr(db.positions, 'find_by_account'):
        print("find_by_account method signature:")
        print(f"  {inspect.signature(db.positions.find_by_account)}")
        
        # Try to get source code
        try:
            source = inspect.getsource(db.positions.find_by_account)
            print("\nfind_by_account source code:")
            print(source)
        except:
            print("  (source code not available)")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()