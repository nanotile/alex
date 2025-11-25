# Module 5: Cloud SQL Database (Demo Configuration)

**Purpose:** Minimal PostgreSQL database for demo/learning deployment

**Cost:** ~$25-40/month (db-f1-micro tier)

---

## What This Deploys

- **Cloud SQL Instance:** PostgreSQL 15 on db-f1-micro (shared CPU, 0.6GB RAM)
- **Database:** `alex` database
- **User:** `alex_admin` with random password
- **Secret Manager:** Password stored securely
- **Backup:** Daily backups at 3 AM UTC

---

## Configuration Choices (Demo Mode)

| Feature | Production | Demo (This) | Savings |
|---------|-----------|-------------|---------|
| **Tier** | db-n1-standard-2 | db-f1-micro | 85% |
| **High Availability** | Yes | No | 50% |
| **Read Replicas** | 1-2 | 0 | 100% |
| **Storage** | 100GB+ | 10GB | 90% |
| **Networking** | Private VPC | Public IP | Simpler |
| **Point-in-time Recovery** | Yes | No | 20% |

**Total Savings:** ~75-85% vs production configuration

---

## Deployment

### Prerequisites

1. Module 0 (Foundation) must be deployed
2. GCP authentication configured
3. Terraform installed

### Deploy

```bash
cd /home/kent_benson/AWS_projects/alex/terraform_GCP/5_database

# Initialize
terraform init

# Review plan
terraform plan

# Deploy (takes ~10-15 minutes)
terraform apply

# Save outputs
terraform output > outputs.txt
```

### Get Database Password

```bash
# Get the connection name
terraform output instance_connection_name

# Get the password from Secret Manager
gcloud secrets versions access latest --secret=alex-demo-db-password
```

---

## Post-Deployment Steps

### 1. Connect to Database

```bash
# Get password first
PASSWORD=$(gcloud secrets versions access latest --secret=alex-demo-db-password)

# Connect via gcloud
gcloud sql connect alex-demo-db --user=alex_admin --database=alex

# Enter password when prompted
```

### 2. Create Schema

```sql
-- Copy schema from AWS deployment
-- File: /home/kent_benson/AWS_projects/alex/backend/database/migrations/001_initial_schema.sql

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    account_id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Instruments table (ETFs, stocks, bonds)
CREATE TABLE IF NOT EXISTS instruments (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    sector TEXT,
    expense_ratio DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    position_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    symbol TEXT NOT NULL REFERENCES instruments(symbol),
    quantity DECIMAL(15,6) NOT NULL,
    cost_basis DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, symbol)
);

-- Jobs table (for async analysis tasks)
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES accounts(account_id) ON DELETE CASCADE,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    request_data JSONB,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_account_id ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
```

### 3. Load Seed Data (Optional)

```bash
# Will create a Python script for this in next step
cd /home/kent_benson/AWS_projects/alex/backend/database
# Coming: load_seed_data_gcp.py
```

---

## Using from Python (Cloud Run)

```python
from google.cloud.sql.connector import Connector
import sqlalchemy
import os

# Initialize connector
connector = Connector()

def get_connection():
    """Create Cloud SQL connection"""
    def getconn():
        return connector.connect(
            os.getenv("CLOUD_SQL_INSTANCE"),  # "project:region:instance"
            "pg8000",
            user=os.getenv("CLOUD_SQL_USER"),
            password=os.getenv("CLOUD_SQL_PASSWORD"),
            db=os.getenv("CLOUD_SQL_DATABASE")
        )

    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )
    return engine

# Usage
engine = get_connection()
with engine.connect() as conn:
    result = conn.execute("SELECT * FROM instruments LIMIT 5")
    for row in result:
        print(row)
```

---

## Cost Management

### Pause Database (When Not Using)

```bash
# Stop instance (keeps data, no compute charges)
gcloud sql instances patch alex-demo-db --activation-policy=NEVER

# Cost when stopped: ~$2/month (storage only)
```

### Resume Database

```bash
# Start instance again
gcloud sql instances patch alex-demo-db --activation-policy=ALWAYS

# Takes ~2-3 minutes to start
```

### Monitor Costs

```bash
# Check current month billing
gcloud billing projects describe gen-lang-client-0259050339

# View detailed billing
# Go to: https://console.cloud.google.com/billing
```

---

## Cleanup

### Destroy Database

```bash
cd /home/kent_benson/AWS_projects/alex/terraform_GCP/5_database

terraform destroy

# Confirm with: yes
```

**Warning:** This will delete all data! Export first if needed.

---

## Differences from AWS Aurora

| Feature | AWS Aurora | GCP Cloud SQL |
|---------|-----------|---------------|
| **API** | Data API (HTTP) | Cloud SQL Connector (library) |
| **VPC** | Not required | Optional (using public IP) |
| **Scaling** | Auto (0.5-1 ACU) | Fixed tier |
| **Backups** | Continuous | Daily snapshots |
| **Cost** | $43-60/month | $25-40/month |
| **Connection** | HTTP requests | PostgreSQL protocol |

---

## Troubleshooting

### Can't connect to database

```bash
# Check instance status
gcloud sql instances describe alex-demo-db --format="value(state)"

# Should show: RUNNABLE

# If not, start it:
gcloud sql instances patch alex-demo-db --activation-policy=ALWAYS
```

### Password not working

```bash
# Get password from Secret Manager
gcloud secrets versions access latest --secret=alex-demo-db-password

# Or reset it:
NEW_PASSWORD=$(openssl rand -base64 32)
gcloud sql users set-password alex_admin \
  --instance=alex-demo-db \
  --password=$NEW_PASSWORD
```

### Connection timeout

```bash
# Check firewall rules
gcloud sql instances describe alex-demo-db \
  --format="json" | jq '.settings.ipConfiguration'

# Your IP should be in authorized networks
# Or use Cloud SQL Proxy for secure connection
```

---

## Next Steps

After database is deployed:

1. **Test connection** from local machine
2. **Load schema** (SQL script above)
3. **Deploy Tagger agent** (Module 6)
4. **Test end-to-end** flow

---

**Estimated Deploy Time:** 10-15 minutes
**Monthly Cost:** $25-40
**Suitable For:** Demo, learning, development
