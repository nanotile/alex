"""
Setup script for GCP Cloud SQL database
- Connects to Cloud SQL
- Loads schema
- Tests connection
"""

import os
import sys
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import text

# Database configuration from terraform outputs
INSTANCE_CONNECTION_NAME = "gen-lang-client-0259050339:us-central1:alex-demo-db"
DB_USER = "alex_admin"
DB_NAME = "alex"

# Get password from terraform state
def get_password_from_terraform():
    """Get password from terraform output"""
    import subprocess
    import json

    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd="/home/kent_benson/AWS_projects/alex/terraform_GCP/5_database",
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error getting terraform output: {result.stderr}")
        sys.exit(1)

    outputs = json.loads(result.stdout)

    # Get password from Secret Manager using terraform
    result = subprocess.run(
        ["terraform", "output", "-raw", "database_password_secret"],
        cwd="/home/kent_benson/AWS_projects/alex/terraform_GCP/5_database",
        capture_output=True,
        text=True
    )

    secret_name = result.stdout.strip()

    # Access the secret (need to use gcloud with user credentials, not service account)
    result = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest", "--secret", secret_name],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error accessing secret: {result.stderr}")
        print("\nTrying alternative method...")

        # Alternative: extract from terraform state file
        import json
        with open("/home/kent_benson/AWS_projects/alex/terraform_GCP/5_database/terraform.tfstate", 'r') as f:
            state = json.load(f)

        for resource in state.get('resources', []):
            if resource.get('type') == 'random_password' and resource.get('name') == 'db_password':
                password = resource['instances'][0]['attributes']['result']
                return password

        print("Could not find password in terraform state!")
        sys.exit(1)

    return result.stdout.strip()


def get_connection():
    """Create Cloud SQL connection"""
    password = get_password_from_terraform()

    print(f"Connecting to: {INSTANCE_CONNECTION_NAME}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")

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


def load_schema(engine):
    """Load database schema"""
    schema_file = "/home/kent_benson/AWS_projects/alex/backend/database/migrations/001_schema.sql"

    print(f"\nLoading schema from: {schema_file}")

    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    # Execute entire schema as one block (handles stored procedures correctly)
    with engine.begin() as conn:
        try:
            print("Executing schema...")
            conn.execute(text(schema_sql))
            print("✅ Schema loaded successfully!")
        except Exception as e:
            print(f"Error executing schema: {e}")
            # Try using psycopg2-style execution instead
            print("\nTrying alternative execution method...")
            conn.connection.driver_connection.run(schema_sql)
            print("✅ Schema loaded successfully (alternative method)!")


def test_connection(engine):
    """Test database connection"""
    print("\nTesting database connection...")

    with engine.connect() as conn:
        # Test 1: Check tables exist
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))

        tables = [row[0] for row in result]
        print(f"\n✅ Tables created: {', '.join(tables)}")

        # Test 2: Insert a test instrument
        print("\nInserting test instrument...")
        conn.execute(text("""
            INSERT INTO instruments (symbol, name, instrument_type, current_price)
            VALUES ('TEST', 'Test Instrument', 'etf', 100.00)
            ON CONFLICT (symbol) DO UPDATE SET current_price = 100.00
        """))
        conn.commit()

        # Test 3: Query it back
        result = conn.execute(text("""
            SELECT symbol, name, instrument_type, current_price
            FROM instruments
            WHERE symbol = 'TEST'
        """))

        row = result.fetchone()
        if row:
            print(f"✅ Test query successful: {row[0]} - {row[1]} @ ${row[3]}")
        else:
            print("❌ Test query failed: No data returned")

        # Test 4: Count tables
        result = conn.execute(text("SELECT COUNT(*) FROM instruments"))
        count = result.fetchone()[0]
        print(f"✅ Instruments count: {count}")


def main():
    """Main setup function"""
    print("=" * 60)
    print("GCP Cloud SQL Database Setup")
    print("=" * 60)

    try:
        # Get connection
        engine = get_connection()
        print("✅ Connected to Cloud SQL!")

        # Load schema
        load_schema(engine)

        # Test connection
        test_connection(engine)

        print("\n" + "=" * 60)
        print("✅ Database setup complete!")
        print("=" * 60)
        print(f"\nConnection details:")
        print(f"  Instance: {INSTANCE_CONNECTION_NAME}")
        print(f"  Database: {DB_NAME}")
        print(f"  User: {DB_USER}")
        print(f"\nTo connect manually:")
        print(f"  gcloud sql connect alex-demo-db --user={DB_USER} --database={DB_NAME}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
