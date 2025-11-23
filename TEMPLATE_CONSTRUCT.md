# Multi-Agent AWS Template Framework - Construction Plan

**Date Created:** 2025-11-23
**Purpose:** Template system to create new multi-agent applications using Alex architecture patterns
**Current Status:** Planning phase - ready to implement

---

## Executive Summary

Alex is approximately **75% reusable infrastructure and patterns**, with only 25% being domain-specific (financial planning) code. This document outlines the plan to extract the reusable portions into a template framework that can generate new multi-agent AWS applications in minutes.

---

## Recommended Approach: Cookiecutter + Shared Library

### Two-Component Strategy

1. **`multi-agent-aws-template`** - Cookiecutter template repository
   - Generates complete project structure
   - Interactive CLI for configuration
   - Includes deployment guides similar to Alex's 8-part guide system

2. **`aws-agent-framework`** - Shared Python library (pip installable)
   - Reusable database clients
   - Base agent patterns
   - Auth utilities
   - Observability helpers

### Why This Approach?

- **Easy for beginners** - One command creates entire project
- **Educational** - Preserves guide-based learning from Alex
- **Flexible** - Generated code is fully customizable
- **Proven pattern** - Used by Django, FastAPI, etc.
- **No magic** - No hidden dependencies or framework lock-in

---

## Developer Experience (Target)

```bash
# 1. Install cookiecutter
pip install cookiecutter

# 2. Generate new app
cookiecutter gh:your-org/multi-agent-aws-template

# Interactive prompts:
# app_name: portfolio-analyzer
# app_description: Multi-agent portfolio analysis platform
# agents: orchestrator, classifier, analyzer, reporter
# aws_region: us-east-1
# bedrock_region: us-west-2
# use_vectors: yes
# auth_provider: clerk
# include_observability: yes

# 3. Project generated with:
# - All terraform modules configured
# - Agent skeletons with TODOs
# - Database schema template
# - Frontend scaffold with auth
# - 8 deployment guides customized to your app
# - Testing framework ready

# 4. Follow guides 1-8 to deploy
cd portfolio-analyzer
# ... follow deployment guides
```

---

## Reusability Analysis

Based on detailed analysis of Alex codebase:

| Component | Reusability | What's Reusable | What's Custom |
|-----------|-------------|-----------------|---------------|
| **Terraform Modules** | 95% | All AWS service configs, IAM patterns | Variable values only |
| **Agent SDK Pattern** | 95% | Lambda handlers, Runner setup, tracing | Instructions, tools |
| **Database Client** | 95% | Data API wrapper, base models | Domain schema |
| **SQS Orchestration** | 95% | Queue setup, job tracking pattern | Business logic |
| **Lambda Packaging** | 100% | Docker build, S3 upload scripts | Agent names |
| **Frontend Auth** | 95% | Clerk integration, JWT verification | UI components |
| **API Backend** | 90% | FastAPI + auth patterns | Domain endpoints |
| **Testing Strategy** | 100% | Dual test approach (simple/full) | Test assertions |
| **Observability** | 100% | LangFuse, CloudWatch setup | Custom metrics |
| **Agent Instructions** | 0% | N/A | Fully domain-specific |
| **Tool Logic** | 20% | Function signatures, context pattern | Business logic |
| **Database Schema** | 60% | Users, jobs, multi-tenant pattern | Domain entities |
| **Frontend UI** | 50% | Layout, navigation, auth flows | Forms, charts |

**Overall: ~75% templatable**

---

## Implementation Plan

### Phase 1: Extract Shared Library (`aws-agent-framework`)

**Create Python package with reusable components:**

```
aws-agent-framework/
├── pyproject.toml
├── README.md
└── aws_agent_framework/
    ├── __init__.py
    ├── database/
    │   ├── __init__.py
    │   ├── client.py          # Data API client (from alex/backend/database)
    │   ├── base_models.py     # BaseModel with CRUD operations
    │   └── utils.py           # Parameter formatting helpers
    ├── agents/
    │   ├── __init__.py
    │   ├── lambda_handler.py  # Reusable handler wrapper
    │   ├── context.py         # Base context patterns
    │   └── testing.py         # Mock utilities, test helpers
    ├── auth/
    │   ├── __init__.py
    │   ├── clerk.py           # JWT verification for Clerk
    │   └── middleware.py      # FastAPI security dependencies
    ├── observability/
    │   ├── __init__.py
    │   ├── langfuse.py        # LangFuse context manager
    │   └── cloudwatch.py      # CloudWatch helpers
    └── packaging/
        ├── __init__.py
        └── docker.py          # Docker packaging utilities
```

**Key Components to Extract:**

1. **Database Client** (`backend/database/src/client.py`)
   - `DataAPIClient` class (lines 1-150)
   - Parameter formatting functions
   - Query/insert/update helpers

2. **Base Models** (`backend/database/src/models.py`)
   - `BaseModel` with `find_by_id`, `create`, `update` patterns
   - Make generic, remove Alex-specific models

3. **Lambda Handler Pattern**
   - Extract common pattern from any agent's `lambda_handler.py`:
     - SQS event parsing
     - Job status updates
     - Error handling
     - Async runner wrapper

4. **Auth Utilities** (`backend/api/lambda_handler.py`)
   - Clerk JWT verification (lines 20-60)
   - FastAPI security dependency
   - User ID extraction

5. **Observability** (from various agents)
   - LangFuse context manager pattern
   - CloudWatch logging helpers
   - Trace decorators

6. **Testing Utilities**
   - Mock Lambda responses
   - Test database fixtures
   - Environment setup helpers

**Deliverable:** Publishable pip package `aws-agent-framework`

---

### Phase 2: Build Cookiecutter Template

**Directory Structure:**

```
multi-agent-aws-template/
├── cookiecutter.json                           # Configuration
├── hooks/
│   ├── pre_gen_project.py                     # Validation
│   └── post_gen_project.py                    # Setup scripts
├── {{cookiecutter.app_name}}/
│   ├── README.md
│   ├── .env.example
│   ├── .gitignore
│   ├── guides/
│   │   ├── 1_permissions.md                   # Parameterized guides
│   │   ├── 2_embeddings.md
│   │   ├── 3_vectors.md
│   │   ├── 4_async_service.md
│   │   ├── 5_database.md
│   │   ├── 6_agents.md
│   │   ├── 7_frontend.md
│   │   └── 8_enterprise.md
│   ├── terraform/
│   │   ├── 1_permissions/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── terraform.tfvars.example       # Pre-filled with app_name
│   │   ├── 2_embeddings/
│   │   │   └── ...                            # All 8 directories
│   │   └── ...
│   ├── backend/
│   │   ├── database/
│   │   │   ├── pyproject.toml
│   │   │   ├── src/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py                  # TODO: Add domain models
│   │   │   │   └── schemas.py                 # TODO: Add Pydantic schemas
│   │   │   └── migrations/
│   │   │       └── 001_schema.sql             # Base + TODO domain tables
│   │   ├── {% for agent in cookiecutter.agents.split(',') %}{{agent.strip()}}/
│   │   │   ├── pyproject.toml                 # With aws-agent-framework dep
│   │   │   ├── agent.py                       # Template with TODOs
│   │   │   ├── lambda_handler.py              # Uses framework base
│   │   │   ├── templates.py                   # TODO: Write instructions
│   │   │   ├── test_simple.py
│   │   │   ├── test_full.py
│   │   │   └── package_docker.py
│   │   ├── {% endfor %}
│   │   └── api/
│   │       ├── pyproject.toml
│   │       ├── lambda_handler.py              # FastAPI with framework auth
│   │       └── routes/
│   │           └── example.py                 # TODO: Add domain routes
│   ├── frontend/
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── .env.local.example
│   │   ├── pages/
│   │   │   ├── _app.tsx                       # Clerk provider
│   │   │   ├── _document.tsx
│   │   │   ├── index.tsx                      # Landing page template
│   │   │   └── dashboard.tsx                  # TODO: Build UI
│   │   ├── components/
│   │   │   └── Layout.tsx
│   │   └── lib/
│   │       ├── api.ts                         # API client with auth
│   │       └── types.ts                       # TODO: Add domain types
│   └── scripts/
│       ├── deploy_frontend.py
│       └── test_all.py
```

**Cookiecutter Configuration (`cookiecutter.json`):**

```json
{
  "app_name": "myapp",
  "app_description": "My multi-agent application",
  "app_name_title": "{{ cookiecutter.app_name.replace('_', ' ').replace('-', ' ').title() }}",

  "aws_region": "us-east-1",
  "bedrock_region": "us-west-2",
  "bedrock_model_id": "us.amazon.nova-pro-v1:0",

  "agents": "orchestrator,classifier,processor",
  "_agent_list": "{{ cookiecutter.agents.split(',') }}",

  "auth_provider": ["clerk", "cognito"],
  "clerk_frontend_api": "",

  "database_type": "aurora-serverless",
  "use_vectors": ["yes", "no"],
  "vector_store": ["s3-vectors", "opensearch"],

  "embedding_service": ["sagemaker", "bedrock-titan"],
  "embedding_model": "huggingface-all-MiniLM-L6-v2",

  "include_async_service": ["no", "yes"],
  "async_service_name": "{{ 'researcher' if cookiecutter.include_async_service == 'yes' else '' }}",

  "include_observability": ["yes", "no"],
  "langfuse_public_key": "",
  "langfuse_secret_key": "",

  "generate_guides": ["full", "quickstart", "minimal"],

  "_template_version": "1.0.0",
  "_aws_agent_framework_version": ">=0.1.0"
}
```

**Post-Generation Hook (`hooks/post_gen_project.py`):**

```python
#!/usr/bin/env python
import os
import subprocess
import shutil

def main():
    app_name = "{{ cookiecutter.app_name }}"
    agents = "{{ cookiecutter.agents }}".split(',')

    print(f"Setting up {app_name}...")

    # 1. Initialize git
    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Initial commit from template"])

    # 2. Initialize uv projects
    directories = [
        "backend/database",
        *[f"backend/{agent.strip()}" for agent in agents],
        "backend/api"
    ]

    for dir_path in directories:
        if os.path.exists(dir_path):
            print(f"Initializing {dir_path}...")
            subprocess.run(["uv", "sync"], cwd=dir_path)

    # 3. Install frontend dependencies
    print("Installing frontend dependencies...")
    subprocess.run(["npm", "install"], cwd="frontend")

    # 4. Create .env from .env.example
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("Created .env file - please configure before deploying")

    # 5. Print next steps
    print("\n" + "="*60)
    print(f"✅ {app_name} created successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review and configure .env file")
    print("2. Follow guides/1_permissions.md to set up AWS")
    print("3. Customize TODOs in:")
    print("   - backend/*/templates.py (agent instructions)")
    print("   - backend/*/agent.py (tools and logic)")
    print("   - backend/database/migrations/001_schema.sql (domain tables)")
    print("   - frontend/pages/dashboard.tsx (UI)")
    print("\nDocumentation: See guides/ directory")
    print("Testing: Run 'uv run test_simple.py' in each backend/{agent}/")
    print("="*60)

if __name__ == "__main__":
    main()
```

---

### Phase 3: Parameterize Key Files

**Example: Agent Template (`backend/{{agent}}/agent.py.jinja`):**

```python
"""
{{ cookiecutter.app_name_title }} - {{agent|capitalize}} Agent

TODO: Customize this agent for your domain.
1. Update INSTRUCTIONS in templates.py
2. Implement tools below
3. Define context schema
"""

from agents import Agent, function_tool, RunContextWrapper
from aws_agent_framework.database import DataAPIClient
from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class {{agent|capitalize}}Context:
    job_id: str
    user_id: str
    # TODO: Add your context fields here
    # Example:
    # domain_data: Dict[str, Any]

# TODO: Implement your tools
@function_tool
async def example_tool(
    wrapper: RunContextWrapper[{{agent|capitalize}}Context],
    param: str
) -> str:
    """
    TODO: Describe what this tool does.

    Args:
        wrapper: Context wrapper with job_id, user_id
        param: Description of parameter

    Returns:
        Result description
    """
    job_id = wrapper.context.job_id
    user_id = wrapper.context.user_id

    # TODO: Implement your logic
    return f"Processed {param}"

def create_agent(job_id: str, user_id: str, data: Dict[str, Any], db: DataAPIClient):
    """Create {{agent}} agent with configured model and tools."""

    # Model configuration
    model_id = os.getenv("BEDROCK_MODEL_ID", "{{ cookiecutter.bedrock_model_id }}")
    bedrock_region = os.getenv("BEDROCK_REGION", "{{ cookiecutter.bedrock_region }}")
    os.environ["AWS_REGION_NAME"] = bedrock_region  # LiteLLM requirement

    from litellm import LitellmModel
    model = LitellmModel(model=f"bedrock/{model_id}")

    # Tools
    tools = [example_tool]  # TODO: Add your tools

    # Context
    context = {{agent|capitalize}}Context(
        job_id=job_id,
        user_id=user_id
        # TODO: Add domain data
    )

    # Task
    task = f"""
    TODO: Format the task for this agent.

    Job ID: {job_id}
    User ID: {user_id}
    """

    return model, tools, task, context
```

**Example: Terraform Variables (`terraform/6_agents/terraform.tfvars.example.jinja`):**

```hcl
# Part 6: {{ cookiecutter.app_name_title }} Agents

# AWS Configuration
aws_region = "{{ cookiecutter.aws_region }}"
account_id = ""  # Auto-detected, leave empty

# Application
app_name = "{{ cookiecutter.app_name }}"

# Dependencies from previous parts
sagemaker_endpoint_name = ""       # From terraform/2_embeddings/terraform output
vector_bucket_name = ""            # From terraform/3_vectors/terraform output
aurora_cluster_arn = ""            # From terraform/5_database/terraform output
aurora_secret_arn = ""             # From terraform/5_database/terraform output

# Agent Configuration
agents = [
  {% for agent in cookiecutter.agents.split(',') %}"{{ agent.strip() }}"{{ "," if not loop.last else "" }}
  {% endfor %}
]

# Bedrock
bedrock_region = "{{ cookiecutter.bedrock_region }}"
bedrock_model_id = "{{ cookiecutter.bedrock_model_id }}"

{% if cookiecutter.include_observability == 'yes' %}
# Observability (optional)
langfuse_public_key = "{{ cookiecutter.langfuse_public_key }}"
langfuse_secret_key = "{{ cookiecutter.langfuse_secret_key }}"
{% endif %}
```

**Example: Database Schema (`backend/database/migrations/001_schema.sql.jinja`):**

```sql
-- {{ cookiecutter.app_name_title }} Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- REUSABLE BASE TABLES (Do not modify)
-- =============================================================================

-- Multi-tenant users ({{ cookiecutter.auth_provider }})
CREATE TABLE users (
    {% if cookiecutter.auth_provider == 'clerk' %}
    clerk_user_id VARCHAR(255) PRIMARY KEY,
    {% else %}
    cognito_user_id VARCHAR(255) PRIMARY KEY,
    {% endif %}
    display_name VARCHAR(255),
    email VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Jobs tracking for async agent processing
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    {% if cookiecutter.auth_provider == 'clerk' %}
    clerk_user_id VARCHAR(255) REFERENCES users ON DELETE CASCADE,
    {% else %}
    cognito_user_id VARCHAR(255) REFERENCES users ON DELETE CASCADE,
    {% endif %}
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    request_payload JSONB,

    -- Agent-specific payloads (one per agent, no merging)
    {% for agent in cookiecutter.agents.split(',') %}
    {{ agent.strip() }}_payload JSONB,
    {% endfor %}
    summary_payload JSONB,

    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_jobs_user ON jobs({% if cookiecutter.auth_provider == 'clerk' %}clerk_user_id{% else %}cognito_user_id{% endif %});
CREATE INDEX idx_jobs_status ON jobs(status);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- DOMAIN-SPECIFIC TABLES (TODO: Customize for your application)
-- =============================================================================

-- TODO: Add your domain tables here
-- Example:
-- CREATE TABLE domain_entities (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     clerk_user_id VARCHAR(255) REFERENCES users ON DELETE CASCADE,
--     name VARCHAR(255) NOT NULL,
--     data JSONB,
--     created_at TIMESTAMP DEFAULT NOW()
-- );
```

**Example: Deployment Guide (`guides/6_agents.md.jinja`):**

````markdown
# Guide 6: {{ cookiecutter.app_name_title }} Agents

## Overview

In this guide, you'll deploy the multi-agent system for {{ cookiecutter.app_name }}.

**Agents to deploy:**
{% for agent in cookiecutter.agents.split(',') %}
- **{{ agent.strip()|capitalize }}**: TODO: Describe purpose
{% endfor %}

**Architecture:**
```
SQS Queue → Orchestrator → Parallel Worker Agents → Results → Database
```

## Prerequisites

- Completed Guides 1-5
- Docker Desktop running
- Agent instructions customized in `backend/*/templates.py`

## Step 1: Customize Agent Logic

Before deploying, you must customize each agent:

{% for agent in cookiecutter.agents.split(',') %}
### {{ agent.strip()|capitalize }} Agent

**File:** `backend/{{ agent.strip() }}/templates.py`

```python
# TODO: Write instructions for {{ agent.strip() }}
INSTRUCTIONS = """
You are a {{ agent.strip() }} specialist for {{ cookiecutter.app_description }}.

Your responsibilities:
1. TODO: Define responsibility 1
2. TODO: Define responsibility 2

Output format: TODO: Define expected output
"""
```

**File:** `backend/{{ agent.strip() }}/agent.py`

Implement your tools following the examples provided.

{% endfor %}

## Step 2: Package Agents

Each agent needs to be packaged for Lambda:

```bash
{% for agent in cookiecutter.agents.split(',') %}
# Package {{ agent.strip() }}
cd backend/{{ agent.strip() }}
uv run package_docker.py
cd ../..

{% endfor %}
```

**Troubleshooting:** If packaging fails, ensure Docker Desktop is running.

## Step 3: Configure Terraform

**File:** `terraform/6_agents/terraform.tfvars`

```bash
cd terraform/6_agents
cp terraform.tfvars.example terraform.tfvars
```

Fill in required values:
- `aurora_cluster_arn` - From `terraform/5_database/terraform output`
- `aurora_secret_arn` - From `terraform/5_database/terraform output`
- `sagemaker_endpoint_name` - From `terraform/2_embeddings/terraform output`

## Step 4: Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

**Resources created:**
- {{ cookiecutter.agents.split(',')|length }} Lambda functions
- 1 SQS queue ({{ cookiecutter.app_name }}-queue)
- IAM roles and policies
- CloudWatch log groups

## Step 5: Test Deployment

### Local Testing (with mocks)

{% for agent in cookiecutter.agents.split(',') %}
```bash
cd backend/{{ agent.strip() }}
uv run test_simple.py
cd ../..
```
{% endfor %}

### AWS Testing (real Lambda)

```bash
{% for agent in cookiecutter.agents.split(',') %}
cd backend/{{ agent.strip() }}
uv run test_full.py
cd ../..
{% endfor %}
```

## Step 6: Verify in AWS Console

1. **Lambda Console** - Verify all {{ cookiecutter.agents.split(',')|length }} functions exist
2. **SQS Console** - Find `{{ cookiecutter.app_name }}-queue`
3. **CloudWatch Logs** - Check `/aws/lambda/{{ cookiecutter.app_name }}-*` for logs

## Step 7: Test End-to-End

Create a test job:

```python
import boto3
import json

sqs = boto3.client('sqs', region_name='{{ cookiecutter.aws_region }}')
queue_url = "https://sqs.{{ cookiecutter.aws_region }}.amazonaws.com/YOUR_ACCOUNT/{{ cookiecutter.app_name }}-queue"

# Send test job
job_payload = {
    "job_id": "test-123",
    "user_id": "test-user",
    # TODO: Add your test data
}

sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps(job_payload)
)

print("Test job sent! Check CloudWatch logs.")
```

## Troubleshooting

**Issue: Lambda timeout**
- Check `timeout` in terraform variables (default 900s for orchestrator)
- Review CloudWatch logs for stuck operations

**Issue: "Access Denied" for Bedrock**
- Verify model access granted in Bedrock console
- Check IAM permissions include `bedrock:InvokeModel`
- Confirm region matches `bedrock_region` variable

**Issue: Database connection failed**
- Verify `aurora_cluster_arn` and `aurora_secret_arn` are correct
- Check IAM role has `rds-data:ExecuteStatement` permission

## Cost Management

**Daily costs (approximate):**
- Lambda: $0.10 - $5.00 (depends on usage)
- SQS: $0.01 - $0.50
- Bedrock: $0.50 - $10.00 (depends on token usage)

**Total: ~$1-15/day while testing**

To minimize costs when not using:
```bash
# Aurora is the main cost - destroyed in Guide 5
cd terraform/5_database
terraform destroy
```

## Next Steps

Proceed to **Guide 7: Frontend & API** to build the user interface.

---

**Need help?** Check CloudWatch logs first, then review the troubleshooting section.
````

---

### Phase 4: Documentation

**Create comprehensive docs:**

1. **Main README.md** (in template repo)
   - What this template does
   - Prerequisites
   - Quick start
   - Configuration options

2. **Generated README.md** (in each app)
   - App-specific setup
   - Architecture overview
   - Deployment checklist
   - Customization guide

3. **CUSTOMIZATION_GUIDE.md**
   - Where to find TODOs
   - How to add agents
   - How to modify database schema
   - How to customize frontend

4. **ARCHITECTURE.md**
   - Explain the patterns
   - Why certain decisions were made
   - How components interact

---

### Phase 5: Testing & Validation

**Test the template by generating sample apps:**

1. **Financial app** (like Alex) - Verify it recreates Alex
2. **E-commerce app** - Different domain (product recommendations)
3. **Healthcare app** - Different domain (patient triage)

**Validation checklist:**
- [ ] Template generates without errors
- [ ] All terraform modules deploy successfully
- [ ] Agents can invoke each other
- [ ] Database migrations run
- [ ] Frontend authenticates with Clerk
- [ ] End-to-end job processing works
- [ ] Tests pass (simple and full)
- [ ] Guides are accurate and complete

---

## Key Design Decisions

### 1. **Cookiecutter Over Custom CLI**

**Why:** Cookiecutter is proven, widely used, and requires no custom maintenance. Developers already know it.

### 2. **Shared Library for Common Code**

**Why:** Avoids duplicating database client, auth logic, etc. in every generated project. Updates propagate via `pip install -U aws-agent-framework`.

### 3. **Independent Terraform Directories**

**Why:** Preserved from Alex for educational value. Students can deploy incrementally and understand each component.

### 4. **Jinja2 Templates with TODOs**

**Why:** Generated code should be immediately useful but clearly marked for customization. TODOs guide developers to required changes.

### 5. **Preserve Guide-Based Learning**

**Why:** Alex's 8-guide structure is pedagogically valuable. Generated guides teach the architecture while being customized to the new app.

### 6. **No Magic, Full Transparency**

**Why:** Generated code should be readable and modifiable. No hidden framework behaviors. Developers own their code.

---

## Files to Extract from Alex

### High Priority (Core Reusability)

1. **`backend/database/src/client.py`** → `aws-agent-framework/database/client.py`
   - Complete Data API client
   - Parameter formatting
   - Query helpers

2. **`backend/database/src/models.py`** → `aws-agent-framework/database/base_models.py`
   - `BaseModel` pattern (remove Alex-specific models)
   - CRUD operations

3. **Any `backend/*/lambda_handler.py`** → `aws-agent-framework/agents/lambda_handler.py`
   - Extract common pattern
   - SQS parsing
   - Job status updates
   - Error handling

4. **`backend/api/lambda_handler.py`** → `aws-agent-framework/auth/clerk.py`
   - JWT verification (lines 20-60)
   - FastAPI dependency

5. **`backend/*/package_docker.py`** → `aws-agent-framework/packaging/docker.py`
   - Docker build logic
   - S3 upload
   - Make configurable

6. **Terraform modules (all 8 directories)** → Template with Jinja2
   - Parameterize app_name, agent names
   - Keep structure identical

### Medium Priority (Enhanced DX)

7. **Testing patterns** → `aws-agent-framework/testing/`
   - Mock utilities from `test_simple.py`
   - AWS test helpers from `test_full.py`

8. **Observability** → `aws-agent-framework/observability/`
   - LangFuse context manager pattern
   - CloudWatch helpers

9. **Frontend patterns** → Template files
   - `_app.tsx` with Clerk
   - `lib/api.ts` API client
   - Layout components

### Low Priority (Nice to Have)

10. **Deployment scripts** → Template
    - `scripts/deploy_frontend.py`
    - Test orchestration scripts

---

## What NOT to Template

**Keep domain-specific in examples/TODOs:**

1. Agent instructions (completely custom)
2. Tool implementations (business logic varies)
3. Database domain tables (entities differ)
4. Frontend UI components (app-specific)
5. Validation schemas (domain rules)
6. Test assertions (depends on logic)

---

## Success Criteria

The template is successful if:

1. **A developer can generate a new multi-agent app in < 5 minutes**
2. **90% of infrastructure "just works" after following guides**
3. **TODOs clearly mark what needs customization**
4. **Generated app can deploy to AWS successfully**
5. **Patterns match Alex (no degradation in architecture quality)**
6. **Documentation is clear for beginners**

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cookiecutter learning curve | Medium | Provide clear examples, use standard patterns |
| Template gets out of sync with AWS changes | High | Version the template, document AWS service versions |
| Too much abstraction in framework | High | Keep framework minimal, prefer generated code |
| TODOs not clear enough | Medium | Add detailed comments, link to examples |
| Terraform version conflicts | Medium | Pin terraform version in docs |

---

## Timeline Estimate

**Phase 1 (Framework):** 2-3 days
- Extract and refactor reusable components
- Create pip package structure
- Write tests

**Phase 2 (Template):** 3-4 days
- Set up cookiecutter structure
- Parameterize all files
- Create hooks

**Phase 3 (Guides):** 2-3 days
- Adapt 8 guides with Jinja2
- Write customization guide
- Create examples

**Phase 4 (Testing):** 2-3 days
- Generate sample apps
- Deploy and validate
- Fix issues

**Phase 5 (Documentation):** 1-2 days
- READMEs
- Architecture docs
- API reference

**Total: ~10-15 days of focused work**

---

## Next Session Tasks

**Immediate next steps:**

1. **Create `aws-agent-framework` repository**
   - Initialize Python package structure
   - Set up pyproject.toml with dependencies

2. **Extract database client**
   - Copy `backend/database/src/client.py`
   - Remove Alex-specific code
   - Add type hints and docstrings

3. **Extract base models**
   - Copy `backend/database/src/models.py`
   - Make `BaseModel` generic
   - Remove domain models

4. **Test extracted components**
   - Write unit tests
   - Verify against Alex database

5. **Create cookiecutter repo**
   - Initialize structure
   - Create `cookiecutter.json`
   - Set up basic template

**By end of day 1, you should have:**
- Empty repos initialized
- Database client extracted and working
- Basic cookiecutter structure

---

## Resources & References

**Cookiecutter:**
- Official docs: https://cookiecutter.readthedocs.io/
- Template examples: https://github.com/cookiecutter/cookiecutter

**Alex Codebase References:**
- Guides: `/home/kent_benson/AWS_projects/alex/guides/`
- Database: `/home/kent_benson/AWS_projects/alex/backend/database/`
- Agents: `/home/kent_benson/AWS_projects/alex/backend/*/`
- Terraform: `/home/kent_benson/AWS_projects/alex/terraform/`

**Similar Projects (for inspiration):**
- Django template: `django-admin startproject`
- FastAPI template: https://github.com/tiangolo/full-stack-fastapi-postgresql
- AWS SAM templates: `sam init`

---

## Questions to Resolve

1. **Naming:** `aws-agent-framework` vs `multi-agent-aws` vs something else?
2. **Versioning:** How to handle breaking changes in AWS services?
3. **License:** MIT? Apache 2.0?
4. **Distribution:** PyPI for framework, GitHub for template?
5. **Maintenance:** Who maintains updates? Community contributions?

---

## Appendix: Detailed Reusability Breakdown

See full analysis document for:
- Line-by-line reusability analysis
- Specific file extraction instructions
- Pattern preservation guidelines
- Migration path from Alex to template

---

**Document Status:** Ready for implementation
**Last Updated:** 2025-11-23
**Next Review:** After Phase 1 completion
