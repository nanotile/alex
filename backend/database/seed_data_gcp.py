#!/usr/bin/env python3
"""
Seed data for Alex Financial Planner - GCP Cloud SQL version
Loads 22 popular ETF instruments with allocation data
"""

import sys
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import text
import json

# Import the instruments data from the AWS version
# We'll extract just the data structure
INSTRUMENTS = [
    # Core US Equity
    {
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "instrument_type": "etf",
        "current_price": 450.25,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "technology": 28, "healthcare": 13, "financials": 13,
            "consumer_discretionary": 12, "industrials": 9, "communication": 9,
            "consumer_staples": 6, "energy": 4, "utilities": 3,
            "real_estate": 2, "materials": 1,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "QQQ",
        "name": "Invesco QQQ Trust",
        "instrument_type": "etf",
        "current_price": 385.50,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "technology": 50, "communication": 17, "consumer_discretionary": 15,
            "healthcare": 8, "consumer_staples": 5, "industrials": 3, "other": 2,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "IWM",
        "name": "iShares Russell 2000 ETF",
        "instrument_type": "etf",
        "current_price": 205.75,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "healthcare": 18, "financials": 17, "industrials": 16, "technology": 14,
            "consumer_discretionary": 12, "real_estate": 7, "energy": 6,
            "materials": 4, "consumer_staples": 3, "utilities": 2, "communication": 1,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "VEA",
        "name": "Vanguard FTSE Developed Markets ETF",
        "instrument_type": "etf",
        "current_price": 48.30,
        "allocation_regions": {"europe": 60, "asia": 35, "oceania": 5},
        "allocation_sectors": {
            "financials": 20, "industrials": 15, "healthcare": 12, "consumer_discretionary": 12,
            "technology": 10, "materials": 9, "consumer_staples": 8, "energy": 6,
            "communication": 4, "utilities": 3, "real_estate": 1,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "VWO",
        "name": "Vanguard FTSE Emerging Markets ETF",
        "instrument_type": "etf",
        "current_price": 42.15,
        "allocation_regions": {"asia": 75, "latin_america": 15, "africa": 5, "europe": 5},
        "allocation_sectors": {
            "technology": 22, "financials": 20, "consumer_discretionary": 14,
            "communication": 12, "materials": 9, "energy": 8, "industrials": 6,
            "healthcare": 4, "consumer_staples": 3, "utilities": 2,
        },
        "allocation_asset_class": {"equity": 100},
    },
    # US Bonds
    {
        "symbol": "AGG",
        "name": "iShares Core U.S. Aggregate Bond ETF",
        "instrument_type": "etf",
        "current_price": 102.50,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "treasury": 40, "mortgage": 30, "corporate": 25, "government_related": 5,
        },
        "allocation_asset_class": {"fixed_income": 100},
    },
    {
        "symbol": "BND",
        "name": "Vanguard Total Bond Market ETF",
        "instrument_type": "etf",
        "current_price": 75.80,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "treasury": 42, "mortgage": 28, "corporate": 24, "government_related": 6,
        },
        "allocation_asset_class": {"fixed_income": 100},
    },
    {
        "symbol": "TLT",
        "name": "iShares 20+ Year Treasury Bond ETF",
        "instrument_type": "etf",
        "current_price": 95.25,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {"treasury": 100},
        "allocation_asset_class": {"fixed_income": 100},
    },
    # Sector ETFs
    {
        "symbol": "XLK",
        "name": "Technology Select Sector SPDR Fund",
        "instrument_type": "etf",
        "current_price": 180.45,
        "allocation_regions": {"north_america": 95, "international": 5},
        "allocation_sectors": {"technology": 100},
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "XLV",
        "name": "Health Care Select Sector SPDR Fund",
        "instrument_type": "etf",
        "current_price": 145.30,
        "allocation_regions": {"north_america": 95, "international": 5},
        "allocation_sectors": {"healthcare": 100},
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "XLF",
        "name": "Financial Select Sector SPDR Fund",
        "instrument_type": "etf",
        "current_price": 38.75,
        "allocation_regions": {"north_america": 95, "international": 5},
        "allocation_sectors": {"financials": 100},
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "XLE",
        "name": "Energy Select Sector SPDR Fund",
        "instrument_type": "etf",
        "current_price": 85.20,
        "allocation_regions": {"north_america": 95, "international": 5},
        "allocation_sectors": {"energy": 100},
        "allocation_asset_class": {"equity": 100},
    },
    # REITs
    {
        "symbol": "VNQ",
        "name": "Vanguard Real Estate ETF",
        "instrument_type": "etf",
        "current_price": 85.60,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {"real_estate": 100},
        "allocation_asset_class": {"real_estate": 100},
    },
    # Commodities
    {
        "symbol": "GLD",
        "name": "SPDR Gold Shares",
        "instrument_type": "etf",
        "current_price": 185.40,
        "allocation_regions": {"global": 100},
        "allocation_sectors": {"commodities": 100},
        "allocation_asset_class": {"commodities": 100},
    },
    {
        "symbol": "DBC",
        "name": "Invesco DB Commodity Index Tracking Fund",
        "instrument_type": "etf",
        "current_price": 22.15,
        "allocation_regions": {"global": 100},
        "allocation_sectors": {"commodities": 100},
        "allocation_asset_class": {"commodities": 100},
    },
    # Balanced/Multi-Asset
    {
        "symbol": "AOR",
        "name": "iShares Core Growth Allocation ETF",
        "instrument_type": "etf",
        "current_price": 52.30,
        "allocation_regions": {"north_america": 60, "international": 30, "global": 10},
        "allocation_sectors": {"diversified": 100},
        "allocation_asset_class": {"equity": 60, "fixed_income": 40},
    },
    {
        "symbol": "AOA",
        "name": "iShares Core Aggressive Allocation ETF",
        "instrument_type": "etf",
        "current_price": 68.75,
        "allocation_regions": {"north_america": 60, "international": 30, "global": 10},
        "allocation_sectors": {"diversified": 100},
        "allocation_asset_class": {"equity": 80, "fixed_income": 20},
    },
    # Additional Popular ETFs
    {
        "symbol": "VOO",
        "name": "Vanguard S&P 500 ETF",
        "instrument_type": "etf",
        "current_price": 415.80,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "technology": 28, "healthcare": 13, "financials": 13,
            "consumer_discretionary": 11, "industrials": 9, "communication": 9,
            "consumer_staples": 6, "energy": 4, "utilities": 3,
            "real_estate": 2, "materials": 2,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "instrument_type": "etf",
        "current_price": 235.90,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "technology": 27, "healthcare": 14, "financials": 13,
            "consumer_discretionary": 11, "industrials": 9, "communication": 8,
            "consumer_staples": 6, "energy": 4, "real_estate": 4,
            "utilities": 2, "materials": 2,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "SCHD",
        "name": "Schwab U.S. Dividend Equity ETF",
        "instrument_type": "etf",
        "current_price": 78.45,
        "allocation_regions": {"north_america": 100},
        "allocation_sectors": {
            "financials": 20, "healthcare": 18, "consumer_staples": 15,
            "industrials": 13, "energy": 10, "technology": 9,
            "utilities": 7, "materials": 5, "consumer_discretionary": 2, "communication": 1,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "VXUS",
        "name": "Vanguard Total International Stock ETF",
        "instrument_type": "etf",
        "current_price": 59.20,
        "allocation_regions": {"europe": 40, "asia": 35, "latin_america": 10,
                              "oceania": 5, "africa": 5, "middle_east": 5},
        "allocation_sectors": {
            "financials": 20, "industrials": 13, "technology": 12,
            "consumer_discretionary": 11, "healthcare": 10, "materials": 9,
            "consumer_staples": 8, "energy": 6, "communication": 6,
            "utilities": 3, "real_estate": 2,
        },
        "allocation_asset_class": {"equity": 100},
    },
    {
        "symbol": "ARKK",
        "name": "ARK Innovation ETF",
        "instrument_type": "etf",
        "current_price": 42.85,
        "allocation_regions": {"north_america": 80, "international": 20},
        "allocation_sectors": {
            "technology": 70, "healthcare": 20, "communication": 5, "other": 5,
        },
        "allocation_asset_class": {"equity": 100},
    },
]


def get_password_from_terraform():
    """Get password from terraform state"""
    import subprocess
    import json

    with open("/home/kent_benson/AWS_projects/alex/terraform_GCP/5_database/terraform.tfstate", 'r') as f:
        state = json.load(f)

    for resource in state.get('resources', []):
        if resource.get('type') == 'random_password' and resource.get('name') == 'db_password':
            password = resource['instances'][0]['attributes']['result']
            return password

    raise Exception("Could not find password in terraform state!")


def get_connection():
    """Create Cloud SQL connection"""
    INSTANCE_CONNECTION_NAME = "gen-lang-client-0259050339:us-central1:alex-demo-db"
    DB_USER = "alex_admin"
    DB_NAME = "alex"

    password = get_password_from_terraform()

    connector = Connector()

    def getconn():
        return connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=password,
            db=DB_NAME
        )

    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )

    return engine


def load_instruments(engine):
    """Load instrument data into database"""
    print(f"Loading {len(INSTRUMENTS)} instruments...")

    with engine.begin() as conn:
        for i, instrument in enumerate(INSTRUMENTS, 1):
            symbol = instrument['symbol']
            name = instrument['name']
            instrument_type = instrument['instrument_type']
            current_price = instrument['current_price']
            allocation_regions = json.dumps(instrument.get('allocation_regions', {}))
            allocation_sectors = json.dumps(instrument.get('allocation_sectors', {}))
            allocation_asset_class = json.dumps(instrument.get('allocation_asset_class', {}))

            # Insert or update instrument
            # Note: Cast the JSON strings to JSONB in PostgreSQL
            query = text("""
                INSERT INTO instruments (
                    symbol, name, instrument_type, current_price,
                    allocation_regions, allocation_sectors, allocation_asset_class
                )
                VALUES (
                    :symbol, :name, :instrument_type, :current_price,
                    CAST(:allocation_regions AS jsonb),
                    CAST(:allocation_sectors AS jsonb),
                    CAST(:allocation_asset_class AS jsonb)
                )
                ON CONFLICT (symbol) DO UPDATE SET
                    name = EXCLUDED.name,
                    instrument_type = EXCLUDED.instrument_type,
                    current_price = EXCLUDED.current_price,
                    allocation_regions = EXCLUDED.allocation_regions,
                    allocation_sectors = EXCLUDED.allocation_sectors,
                    allocation_asset_class = EXCLUDED.allocation_asset_class,
                    updated_at = NOW()
            """)

            conn.execute(query, {
                'symbol': symbol,
                'name': name,
                'instrument_type': instrument_type,
                'current_price': current_price,
                'allocation_regions': allocation_regions,
                'allocation_sectors': allocation_sectors,
                'allocation_asset_class': allocation_asset_class,
            })

            print(f"  {i:2d}. ✅ {symbol:6s} - {name}")

    print(f"\n✅ Loaded {len(INSTRUMENTS)} instruments successfully!")


def verify_data(engine):
    """Verify data was loaded correctly"""
    print("\nVerifying data...")

    with engine.connect() as conn:
        # Count instruments
        result = conn.execute(text("SELECT COUNT(*) FROM instruments"))
        count = result.fetchone()[0]
        print(f"✅ Total instruments: {count}")

        # Sample a few instruments
        result = conn.execute(text("""
            SELECT symbol, name, instrument_type, current_price
            FROM instruments
            ORDER BY symbol
            LIMIT 5
        """))

        print("\nSample instruments:")
        for row in result:
            print(f"  {row[0]:6s} - {row[1]:40s} @ ${row[3]}")

        # Check allocation data
        result = conn.execute(text("""
            SELECT symbol, allocation_asset_class
            FROM instruments
            WHERE symbol = 'SPY'
        """))

        row = result.fetchone()
        if row:
            print(f"\nSPY allocation check:")
            print(f"  Asset class: {row[1]}")


def main():
    """Main function"""
    print("=" * 60)
    print("Loading Seed Data - GCP Cloud SQL")
    print("=" * 60)

    try:
        engine = get_connection()
        print("✅ Connected to Cloud SQL!")

        load_instruments(engine)
        verify_data(engine)

        print("\n" + "=" * 60)
        print("✅ Seed data loading complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
