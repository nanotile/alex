#!/usr/bin/env python3
"""
Database Confirmation Script
Verifies that test data was created 

https://claude.ai/chat/08d7fb36-f490-49e8-873f-d195f4a7ddb3
"""

from src.client import DataAPIClient
from src.models import Database
from decimal import Decimal
from typing import Dict, List, Any


def format_currency(amount) -> str:
    """Format decimal as currency"""
    if isinstance(amount, str):
        amount = Decimal(amount)
    return f"${amount:,.2f}"


def format_percent(rate) -> str:
    """Format decimal as percentage"""
    if isinstance(rate, str):
        rate = Decimal(rate)
    return f"{(rate * 100):.2f}%"


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_item(label: str, value: Any, indent: int = 1):
    """Print an item with label"""
    spaces = "  " * indent
    print(f"{spaces}• {label}: {value}")


def confirm_user(db_models: Database, clerk_user_id: str) -> bool:
    """Confirm test user exists and has correct attributes"""
    print_section("👤 USER VERIFICATION")
    
    user = db_models.users.find_by_clerk_id(clerk_user_id)
    
    if not user:
        print("  ❌ Test user NOT found!")
        return False
    
    print(f"  ✅ User found: {user['display_name']}")
    print_item("Clerk ID", user['clerk_user_id'])
    print_item("Display Name", user['display_name'])
    print_item("Years Until Retirement", user['years_until_retirement'])
    print_item("Target Retirement Income", format_currency(user['target_retirement_income']))
    print_item("Created At", user['created_at'])
    
    # Verify expected values
    issues = []
    if user['display_name'] != 'Test User':
        issues.append(f"Expected display_name 'Test User', got '{user['display_name']}'")
    if user['years_until_retirement'] != 25:
        issues.append(f"Expected 25 years until retirement, got {user['years_until_retirement']}")
    
    # Handle potential string conversion for Decimal comparison
    target_income = user['target_retirement_income']
    if isinstance(target_income, str):
        target_income = Decimal(target_income)
    if target_income != Decimal('100000'):
        issues.append(f"Expected target income $100,000, got {format_currency(target_income)}")
    
    if issues:
        print("\n  ⚠️  Issues found:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    
    return True


def confirm_accounts(db_models: Database, clerk_user_id: str) -> tuple[bool, List[int]]:
    """Confirm test accounts exist with correct attributes"""
    print_section("💰 ACCOUNTS VERIFICATION")
    
    accounts = db_models.accounts.find_by_user(clerk_user_id)
    
    if not accounts:
        print("  ❌ No accounts found!")
        return False, []
    
    print(f"  ✅ Found {len(accounts)} accounts\n")
    
    expected_accounts = {
        '401(k)': {
            'purpose': 'Primary retirement savings',
            'cash_balance': Decimal('5000'),
            'cash_interest': Decimal('0.045')
        },
        'Roth IRA': {
            'purpose': 'Tax-free retirement savings',
            'cash_balance': Decimal('1000'),
            'cash_interest': Decimal('0.04')
        },
        'Taxable Brokerage': {
            'purpose': 'General investment account',
            'cash_balance': Decimal('2500'),
            'cash_interest': Decimal('0.035')
        }
    }
    
    account_ids = []
    all_valid = True
    
    for i, account in enumerate(accounts, 1):
        account_ids.append(account['id'])
        account_name = account['account_name']
        
        print(f"  Account {i}: {account_name}")
        print_item("ID", account['id'], indent=2)
        print_item("Purpose", account['account_purpose'], indent=2)
        print_item("Cash Balance", format_currency(account['cash_balance']), indent=2)
        print_item("Cash Interest", format_percent(account['cash_interest']), indent=2)
        
        # Verify expected values
        if account_name in expected_accounts:
            expected = expected_accounts[account_name]
            issues = []
            
            if account['account_purpose'] != expected['purpose']:
                issues.append(f"Wrong purpose: expected '{expected['purpose']}'")
            
            # Handle potential string conversion for Decimal comparisons
            cash_balance = account['cash_balance']
            if isinstance(cash_balance, str):
                cash_balance = Decimal(cash_balance)
            if cash_balance != expected['cash_balance']:
                issues.append(f"Wrong balance: expected {format_currency(expected['cash_balance'])}")
            
            cash_interest = account['cash_interest']
            if isinstance(cash_interest, str):
                cash_interest = Decimal(cash_interest)
            if cash_interest != expected['cash_interest']:
                issues.append(f"Wrong interest: expected {format_percent(expected['cash_interest'])}")
            
            if issues:
                print("    ⚠️  Issues:")
                for issue in issues:
                    print(f"      - {issue}")
                all_valid = False
            else:
                print("    ✅ All attributes correct")
        else:
            print(f"    ⚠️  Unexpected account name: {account_name}")
            all_valid = False
        
        print()
    
    # Check if all expected accounts exist
    found_names = {acc['account_name'] for acc in accounts}
    missing = set(expected_accounts.keys()) - found_names
    
    if missing:
        print(f"  ⚠️  Missing accounts: {', '.join(missing)}")
        all_valid = False
    
    if len(accounts) != 3:
        print(f"  ⚠️  Expected 3 accounts, found {len(accounts)}")
        all_valid = False
    
    return all_valid, account_ids


def confirm_positions(db_models: Database, account_id: int) -> bool:
    """Confirm test positions exist in the first account"""
    print_section("📊 POSITIONS VERIFICATION")
    
    positions = db_models.positions.find_by_account(account_id)
    
    if not positions:
        print(f"  ❌ No positions found for account ID {account_id}!")
        return False
    
    print(f"  ✅ Found {len(positions)} positions in 401(k) account\n")
    
    expected_positions = {
        'SPY': Decimal('100'),
        'QQQ': Decimal('50'),
        'BND': Decimal('200'),
        'VEA': Decimal('150'),
        'GLD': Decimal('25')
    }
    
    all_valid = True
    total_value = Decimal('0')
    
    for i, position in enumerate(positions, 1):
        symbol = position['symbol']
        quantity = position['quantity']
        
        print(f"  Position {i}: {symbol}")
        print_item("Symbol", symbol, indent=2)
        print_item("Quantity", f"{quantity} shares", indent=2)
        print_item("Account ID", position['account_id'], indent=2)
        
        # Verify expected values
        if symbol in expected_positions:
            expected_qty = expected_positions[symbol]
            
            # Handle potential string conversion for Decimal comparison
            actual_qty = quantity
            if isinstance(actual_qty, str):
                actual_qty = Decimal(actual_qty)
            
            if actual_qty != expected_qty:
                print(f"    ⚠️  Wrong quantity: expected {expected_qty}, got {actual_qty}")
                all_valid = False
            else:
                print("    ✅ Correct quantity")
        else:
            print(f"    ⚠️  Unexpected symbol: {symbol}")
            all_valid = False
        
        print()
    
    # Check if all expected positions exist
    found_symbols = {pos['symbol'] for pos in positions}
    missing = set(expected_positions.keys()) - found_symbols
    
    if missing:
        print(f"  ⚠️  Missing positions: {', '.join(missing)}")
        all_valid = False
    
    if len(positions) != 5:
        print(f"  ⚠️  Expected 5 positions, found {len(positions)}")
        all_valid = False
    
    return all_valid


def confirm_instruments(db: DataAPIClient) -> bool:
    """Confirm instruments were loaded"""
    print_section("🎵 INSTRUMENTS VERIFICATION")
    
    result = db.query("SELECT COUNT(*) as count FROM instruments")
    count = result[0]['count'] if result else 0
    
    print(f"  Total instruments loaded: {count}")
    
    if count == 22:
        print("  ✅ Correct number of instruments (22)")
        
        # Show a sample of instruments
        sample = db.query("SELECT symbol, name FROM instruments LIMIT 5")
        if sample:
            print("\n  Sample instruments:")
            for inst in sample:
                print_item(inst['symbol'], inst['name'], indent=2)
        
        return True
    else:
        print(f"  ⚠️  Expected 22 instruments, found {count}")
        return False


def confirm_table_counts(db: DataAPIClient):
    """Show record counts for all tables"""
    print_section("📈 TABLE RECORD COUNTS")
    
    tables = ['users', 'instruments', 'accounts', 'positions', 'jobs']
    
    for table in tables:
        result = db.query(f"SELECT COUNT(*) as count FROM {table}")
        count = result[0]['count'] if result else 0
        print_item(table.upper(), f"{count} records")


def main():
    print("🔍 Database Confirmation Script")
    print("=" * 60)
    
    # Initialize database connections
    db = DataAPIClient()
    db_models = Database()
    
    # Test data identifiers
    test_user_id = 'test_user_001'
    
    # Run confirmations
    results = {
        'user': False,
        'accounts': False,
        'positions': False,
        'instruments': False
    }
    
    # Confirm user
    results['user'] = confirm_user(db_models, test_user_id)
    
    # Confirm accounts
    accounts_valid, account_ids = confirm_accounts(db_models, test_user_id)
    results['accounts'] = accounts_valid
    
    # Confirm positions (in 401(k) account)
    # Get the accounts list to find 401(k)
    accounts = db_models.accounts.find_by_user(test_user_id)
    if accounts:
        # Find the 401(k) account specifically
        account_401k = next((acc for acc in accounts if acc['account_name'] == '401(k)'), None)
        if account_401k:
            results['positions'] = confirm_positions(db_models, account_401k['id'])
        else:
            print_section("📊 POSITIONS VERIFICATION")
            print("  ⚠️  Cannot verify positions - 401(k) account not found")
    else:
        print_section("📊 POSITIONS VERIFICATION")
        print("  ⚠️  Cannot verify positions - no accounts found")
    
    # Confirm instruments
    results['instruments'] = confirm_instruments(db)
    
    # Show table counts
    confirm_table_counts(db)
    
    # Final summary
    print_section("✅ VERIFICATION SUMMARY")
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {check.upper():.<20} {status}")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 All verifications PASSED! Database is correctly set up.")
        return 0
    else:
        print("⚠️  Some verifications FAILED. Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())