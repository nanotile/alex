#!/usr/bin/env python3
"""
Debug Positions Script
Shows detailed information about positions in the database
https://claude.ai/chat/08d7fb36-f490-49e8-873f-d195f4a7ddb3
"""

from src.client import DataAPIClient
from src.models import Database
from decimal import Decimal


def main():
    print("🔍 Debugging Positions\n")
    print("=" * 80)
    
    db = DataAPIClient()
    db_models = Database()
    
    # Get test user
    user = db_models.users.find_by_clerk_id('test_user_001')
    if not user:
        print("❌ Test user not found!")
        return
    
    print(f"✅ Found user: {user['display_name']}\n")
    
    # Get accounts
    accounts = db_models.accounts.find_by_user('test_user_001')
    print(f"Found {len(accounts)} accounts:\n")
    
    for i, account in enumerate(accounts, 1):
        print(f"Account {i}: {account['account_name']} (ID: {account['id']})")
        
        # Get positions for this account
        positions = db_models.positions.find_by_account(account['id'])
        print(f"  Positions in this account: {len(positions)}")
        
        if positions:
            print(f"\n  {'Symbol':<10} {'Quantity':<15} {'Type':<15}")
            print(f"  {'-'*40}")
            
            for pos in positions:
                symbol = pos['symbol']
                quantity = pos['quantity']
                qty_type = type(quantity).__name__
                
                print(f"  {symbol:<10} {str(quantity):<15} {qty_type:<15}")
                
                # Show raw value and comparison
                print(f"    Raw value: {repr(quantity)}")
                
                # Try converting if it's a string
                if isinstance(quantity, str):
                    try:
                        decimal_qty = Decimal(quantity)
                        print(f"    As Decimal: {decimal_qty}")
                    except:
                        print(f"    ⚠️  Cannot convert to Decimal")
        
        print()
    
    # Raw SQL query to see exactly what's in the database
    print("\n" + "=" * 80)
    print("RAW DATABASE QUERY")
    print("=" * 80)
    
    raw_positions = db.query("""
        SELECT 
            p.id,
            p.account_id,
            p.symbol,
            p.quantity,
            a.account_name
        FROM positions p
        JOIN accounts a ON p.account_id = a.id
        WHERE a.clerk_user_id = 'test_user_001'
        ORDER BY a.account_name, p.symbol
    """)
    
    if raw_positions:
        print(f"\nFound {len(raw_positions)} total positions:\n")
        for pos in raw_positions:
            print(f"ID: {pos['id']}")
            print(f"  Account: {pos['account_name']} (ID: {pos['account_id']})")
            print(f"  Symbol: {pos['symbol']}")
            print(f"  Quantity: {pos['quantity']} (type: {type(pos['quantity']).__name__})")
            print()
    else:
        print("\n❌ No positions found in database!")
    
    # Check expected vs actual
    print("=" * 80)
    print("EXPECTED VS ACTUAL")
    print("=" * 80)
    
    expected_positions = {
        'SPY': Decimal('100'),
        'QQQ': Decimal('50'),
        'BND': Decimal('200'),
        'VEA': Decimal('150'),
        'GLD': Decimal('25')
    }
    
    if accounts:
        # Find the 401(k) account
        account_401k = next((acc for acc in accounts if acc['account_name'] == '401(k)'), None)
        
        if not account_401k:
            print("\n❌ 401(k) account not found!")
            return
        
        account_401k_id = account_401k['id']
        actual_positions = db_models.positions.find_by_account(account_401k_id)
        
        print(f"\n401(k) account ID: {account_401k_id}")
        print(f"Expected {len(expected_positions)} positions")
        print(f"Found {len(actual_positions)} positions\n")
        
        # Create actual dict
        actual_dict = {}
        for pos in actual_positions:
            symbol = pos['symbol']
            qty = pos['quantity']
            if isinstance(qty, str):
                qty = Decimal(qty)
            actual_dict[symbol] = qty
        
        # Compare
        all_symbols = set(expected_positions.keys()) | set(actual_dict.keys())
        
        print(f"{'Symbol':<10} {'Expected':<15} {'Actual':<15} {'Match':<10}")
        print("-" * 50)
        
        for symbol in sorted(all_symbols):
            expected = expected_positions.get(symbol, "MISSING")
            actual = actual_dict.get(symbol, "MISSING")
            
            if expected == "MISSING" or actual == "MISSING":
                match = "❌"
            elif expected == actual:
                match = "✅"
            else:
                match = "❌"
            
            print(f"{symbol:<10} {str(expected):<15} {str(actual):<15} {match:<10}")


if __name__ == "__main__":
    main()