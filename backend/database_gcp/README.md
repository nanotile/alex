# Alex Database Library - GCP Cloud SQL

Simplified database library for GCP Cloud Run services.

## Usage

```python
from database_gcp import CloudSQLClient

# Initialize (reads from environment variables)
client = CloudSQLClient()

# Query
instruments = client.query("SELECT * FROM instruments WHERE symbol = :symbol", {"symbol": "SPY"})

# Execute
client.execute(
    "INSERT INTO instruments (symbol, name) VALUES (:symbol, :name)",
    {"symbol": "TEST", "name": "Test Instrument"}
)
```

## Environment Variables

- `CLOUD_SQL_INSTANCE` - Connection name (project:region:instance)
- `CLOUD_SQL_DATABASE` - Database name (default: alex)
- `CLOUD_SQL_USER` - Database user
- `CLOUD_SQL_PASSWORD` - Database password

## Differences from AWS Version

| AWS Aurora | GCP Cloud SQL |
|------------|---------------|
| Data API (HTTP) | Cloud SQL Connector (library) |
| boto3 client | google-cloud-sql-connector |
| No connection pooling needed | Built-in connection pooling |
| IAM authentication | Username + password |

## Installation

```bash
uv add cloud-sql-python-connector pg8000 sqlalchemy
```
