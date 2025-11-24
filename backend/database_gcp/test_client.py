#!/usr/bin/env python3
"""
Test the GCP database client
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.client import CloudSQLClient
from src.models import Instrument


def get_password_from_terraform():
    """Get password from terraform state"""
    import json

    with open("/home/kent_benson/AWS_projects/alex/terraform_GCP/5_database/terraform.tfstate", 'r') as f:
        state = json.load(f)

    for resource in state.get('resources', []):
        if resource.get('type') == 'random_password' and resource.get('name') == 'db_password':
            return resource['instances'][0]['attributes']['result']

    raise Exception("Could not find password!")


def main():
    """Test the client"""
    print("=" * 60)
    print("Testing GCP Database Client")
    print("=" * 60)

    # Set environment variables
    os.environ['CLOUD_SQL_INSTANCE'] = 'gen-lang-client-0259050339:us-central1:alex-demo-db'
    os.environ['CLOUD_SQL_DATABASE'] = 'alex'
    os.environ['CLOUD_SQL_USER'] = 'alex_admin'
    os.environ['CLOUD_SQL_PASSWORD'] = get_password_from_terraform()

    # Create client
    client = CloudSQLClient()
    print("✅ Client created\n")

    # Test 1: Query instruments
    print("Test 1: Query all instruments")
    instruments = client.query("SELECT symbol, name, current_price FROM instruments ORDER BY symbol LIMIT 5")
    print(f"✅ Found {len(instruments)} instruments")
    for inst in instruments:
        print(f"  {inst['symbol']:6s} - {inst['name']:40s} @ ${inst['current_price']}")

    # Test 2: Query specific instrument
    print("\nTest 2: Query SPY with allocations")
    spy = client.query(
        "SELECT * FROM instruments WHERE symbol = :symbol",
        {"symbol": "SPY"}
    )
    if spy:
        inst = spy[0]
        print(f"✅ Found SPY")
        print(f"  Name: {inst['name']}")
        print(f"  Price: ${inst['current_price']}")
        print(f"  Asset Class: {inst['allocation_asset_class']}")
        print(f"  Regions: {inst['allocation_regions']}")

    # Test 3: Count instruments
    print("\nTest 3: Count instruments by type")
    counts = client.query("""
        SELECT instrument_type, COUNT(*) as count
        FROM instruments
        GROUP BY instrument_type
        ORDER BY count DESC
    """)
    print("✅ Instrument types:")
    for row in counts:
        print(f"  {row['instrument_type']:15s}: {row['count']}")

    # Test 4: Create Instrument model
    print("\nTest 4: Create Instrument model from data")
    inst_data = client.query("SELECT * FROM instruments WHERE symbol = 'QQQ'")[0]
    qqq = Instrument.from_dict(inst_data)
    print(f"✅ Created Instrument model")
    print(f"  Symbol: {qqq.symbol}")
    print(f"  Name: {qqq.name}")
    print(f"  Price: ${qqq.current_price}")

    # Close client
    client.close()
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
