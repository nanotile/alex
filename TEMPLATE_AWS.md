# Alex Multi-Agent Framework Template

## Overview

This document outlines the plan to transform Alex from a financial portfolio analysis application into a reusable, modular multi-agent framework. The framework will support:

- **Dynamic agent orchestration** - Runtime agent selection based on input context
- **Hybrid configuration** - YAML for infrastructure, Python for agent logic
- **Pluggable infrastructure** - Swap databases, queues, and services as needed
- **Domain flexibility** - Work with different analytical domains beyond finance

## Current State: Alex Architecture

Alex is a production-grade multi-agent SaaS application with:
- 5 specialized agents (Planner, Tagger, Reporter, Charter, Retirement)
- Aurora Serverless v2 PostgreSQL database
- SQS-based orchestration
- Lambda execution environment
- OpenAI Agents SDK for agent implementation
- AWS Bedrock (Nova Pro) for LLM capabilities

**Key Pattern**: Job-based async processing where:
1. Frontend creates job → SQS queue
2. Planner (orchestrator) coordinates other agents
3. Agents run in parallel and store results in database
4. Frontend polls job status until completion

## Target State: Reusable Framework

A modular framework that allows developers to:
1. Define new agents via configuration + minimal code
2. Deploy multi-agent systems in different domains
3. Customize infrastructure components (database, queue, storage)
4. Use dynamic orchestration (agents selected at runtime)

---

## Implementation Plan

### Phase 1: Extract Core Framework (Week 1)

#### 1.1 Create Framework Package Structure

```
agent_framework/
├── core/
│   ├── base_agent.py         # Abstract Agent base class
│   ├── base_handler.py       # Lambda handler boilerplate
│   ├── orchestrator.py       # Dynamic agent selection logic
│   └── job_manager.py        # Job lifecycle management
├── infrastructure/
│   ├── database.py           # Abstract DB interface
│   ├── queue.py              # Abstract queue interface
│   └── storage.py            # Abstract storage interface
├── config/
│   ├── agent_config.py       # Agent configuration schemas
│   ├── loader.py             # YAML config loader
│   └── validators.py         # Config validation
├── terraform_modules/
│   ├── agent_lambda/         # Parameterized Lambda module
│   ├── orchestrator/         # SQS + orchestrator module
│   └── database/             # Optional DB module
└── observability/
    ├── tracing.py            # Framework tracing
    └── metrics.py            # Standard metrics
```

#### 1.2 Extract Common Components

**From Alex's current codebase:**

1. **Database Package** (`backend/database/`)
   - Already a separate uv project
   - Extract into framework as reference implementation
   - Create abstract interface for multiple DB backends

2. **Observability Module** (`observability.py`)
   - Identical across all agents
   - Move to framework with LangFuse/Logfire integration
   - Make observability providers pluggable

3. **Packaging System** (`package_docker.py`)
   - 95% identical across agents
   - Generalize into framework CLI tool
   - Support multiple packaging strategies

4. **Lambda Handler Pattern**
   - Extract common boilerplate from `lambda_handler.py`
   - Create base class with hooks for agent-specific logic
   - Handle SQS events, direct invocations, error handling

**Common patterns to preserve:**

```python
# Standard Lambda handler pattern
async def lambda_handler(event, context):
    with observe():
        job_id = extract_job_id(event)
        result = await run_agent(job_id)
        return standardized_response(result)

# Standard agent execution pattern
async def run_agent(job_id):
    model, tools, task = create_agent(job_id)

    with trace("Agent Name"):
        agent = Agent(
            name="Agent Name",
            instructions=AGENT_INSTRUCTIONS,
            model=model,
            tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            max_turns=20
        )

        return result.final_output
```

---

### Phase 2: Create Agent Configuration System (Week 1-2)

#### 2.1 Agent Definition Format

Create `agents.yaml` specification for declaring agents:

```yaml
# Project metadata
project:
  name: my-analytics-platform
  version: 1.0.0
  region: us-east-1

# Agent definitions
agents:
  # Worker agent example
  data_cleaner:
    type: worker
    description: "Cleans and normalizes input data"

    runtime:
      timeout: 300
      memory: 1024
      environment:
        - DATABASE_URL
        - CUSTOM_API_KEY

    capabilities:
      tools:
        - validate_schema
        - remove_outliers
      structured_output: true
      output_schema: CleanedDataOutput
      context_type: DataCleanerContext

    dependencies:
      database: read-write
      storage: required
      external_apis:
        - data_validation_service

    outputs:
      database_field: cleaned_data

  # Orchestrator agent example
  analytics_planner:
    type: orchestrator
    description: "Coordinates analytics workflow"

    runtime:
      timeout: 900
      memory: 2048
      triggers:
        - sqs_queue

    capabilities:
      tools:
        - invoke_data_cleaner
        - invoke_analyzer
        - invoke_reporter

    dependencies:
      database: read-write
      queue: required

# Orchestration strategy
orchestration:
  strategy: dynamic  # dynamic|sequential|parallel

  # Dynamic selection rules
  selection_rules:
    # Rule 1: Financial data workflow
    - name: financial_analysis
      condition: "input.data_type == 'financial'"
      agents:
        - sequential: [data_cleaner, financial_analyzer]
        - parallel: [risk_calculator, compliance_checker]
        - sequential: [reporter]

    # Rule 2: Marketing data workflow
    - name: marketing_analysis
      condition: "input.data_type == 'marketing'"
      agents:
        - sequential: [data_cleaner, marketing_analyzer]
        - parallel: [segment_analyzer, campaign_optimizer]
        - sequential: [reporter]

    # Rule 3: Low confidence requires validation
    - name: validation_required
      condition: "prev_step.confidence < 0.7"
      agents: [validator, manual_review_notifier]

    # Rule 4: Always run at end
    - name: final_steps
      condition: "always"
      agents: [reporter, notifier]

# Infrastructure configuration
infrastructure:
  database:
    provider: aurora-serverless-v2  # aurora-serverless-v2|rds-postgres|dynamodb
    config:
      engine: postgresql
      min_capacity: 0.5
      max_capacity: 1.0

  queue:
    provider: sqs  # sqs|eventbridge|custom
    config:
      visibility_timeout: 900

  storage:
    provider: s3  # s3|efs|custom
    config:
      bucket_prefix: analytics-data

# Optional: LLM configuration
llm:
  provider: bedrock  # bedrock|openai|anthropic
  model: us.amazon.nova-pro-v1:0
  region: us-east-1
  fallback_model: us.amazon.nova-lite-v1:0
```

#### 2.2 Agent Registry Pattern

**Core registry implementation:**

```python
from typing import Dict, List, Optional, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class AgentConfig:
    name: str
    type: str  # worker|orchestrator
    timeout: int
    memory: int
    tools: List[str]
    dependencies: Dict[str, str]
    output_field: str

class AgentRegistry:
    """Central registry for all agents in the system"""

    def __init__(self):
        self._agents: Dict[str, AgentConfig] = {}
        self._agent_classes: Dict[str, Type] = {}
        self._rules_engine = None

    def register(self, name: str, agent_class: Type, config: AgentConfig):
        """Register an agent with the framework"""
        self._agents[name] = config
        self._agent_classes[name] = agent_class

    def get_agent(self, name: str) -> Optional[Type]:
        """Get agent class by name"""
        return self._agent_classes.get(name)

    def get_config(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration"""
        return self._agents.get(name)

    def list_agents(self, agent_type: Optional[str] = None) -> List[str]:
        """List all registered agents, optionally filtered by type"""
        if agent_type:
            return [
                name for name, config in self._agents.items()
                if config.type == agent_type
            ]
        return list(self._agents.keys())

    def get_available_agents(self, job_context: dict) -> List[str]:
        """Get agents available for a given job context"""
        if not self._rules_engine:
            return self.list_agents(agent_type="worker")

        return self._rules_engine.evaluate(job_context)

    def create_orchestration_plan(self, input_data: dict) -> List[dict]:
        """
        Create execution plan based on input data and orchestration rules

        Returns:
            List of execution steps, e.g.:
            [
                {"type": "sequential", "agents": ["cleaner", "validator"]},
                {"type": "parallel", "agents": ["analyzer1", "analyzer2"]},
                {"type": "sequential", "agents": ["reporter"]}
            ]
        """
        if not self._rules_engine:
            # Default: run all workers in parallel
            workers = self.list_agents(agent_type="worker")
            return [{"type": "parallel", "agents": workers}]

        return self._rules_engine.create_plan(input_data)

# Usage in agent code
registry = AgentRegistry()

# Decorator for easy registration
def agent(name: str, config: dict):
    def decorator(cls):
        agent_config = AgentConfig(**config)
        registry.register(name, cls, agent_config)
        return cls
    return decorator

# Example usage
@agent(name="data_cleaner", config={
    "type": "worker",
    "timeout": 300,
    "memory": 1024,
    "tools": ["validate_schema"],
    "dependencies": {"database": "read-write"},
    "output_field": "cleaned_data"
})
class DataCleanerAgent(BaseAgent):
    async def run(self, job_id: str):
        # Implementation
        pass
```

#### 2.3 Rules Engine for Dynamic Orchestration

```python
from typing import Any, Dict, List
import re

class RulesEngine:
    """Evaluates orchestration rules and creates execution plans"""

    def __init__(self, rules: List[Dict]):
        self.rules = rules

    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate a condition string against context

        Examples:
            condition="input.data_type == 'financial'"
            condition="prev_step.confidence < 0.7"
            condition="always"
        """
        if condition == "always":
            return True

        # Simple expression evaluator (can be enhanced with safe_eval)
        # For production, use a proper expression language like JMESPath
        try:
            # Replace dotted paths with dict lookups
            expr = condition
            for key in re.findall(r'\w+\.\w+(?:\.\w+)*', condition):
                parts = key.split('.')
                value = context
                for part in parts:
                    value = value.get(part, {})
                expr = expr.replace(key, repr(value))

            return eval(expr)
        except:
            return False

    def create_plan(self, context: Dict[str, Any]) -> List[Dict]:
        """Create execution plan based on matching rules"""
        plan = []

        for rule in self.rules:
            condition = rule.get("condition", "always")

            if self.evaluate_condition(condition, context):
                agents_config = rule.get("agents", [])

                # Parse agent configuration
                if isinstance(agents_config, list):
                    for item in agents_config:
                        if isinstance(item, str):
                            plan.append({"type": "sequential", "agents": [item]})
                        elif isinstance(item, dict):
                            plan.append(item)

        return plan
```

---

### Phase 3: Database Abstraction (Week 2)

#### 3.1 Create Database Interface

**Abstract database provider:**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class DatabaseProvider(ABC):
    """Abstract interface for database operations"""

    @abstractmethod
    async def create_job(
        self,
        user_id: str,
        job_type: str,
        request_payload: Dict[str, Any]
    ) -> str:
        """Create a new job and return job_id"""
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID with all agent results"""
        pass

    @abstractmethod
    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None
    ):
        """Update job status"""
        pass

    @abstractmethod
    async def store_agent_output(
        self,
        job_id: str,
        agent_name: str,
        output_payload: Dict[str, Any]
    ):
        """Store output from a specific agent"""
        pass

    @abstractmethod
    async def get_agent_output(
        self,
        job_id: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get output from a specific agent"""
        pass

    @abstractmethod
    async def list_jobs(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List jobs for a user"""
        pass
```

**Implementation for Aurora (existing Alex pattern):**

```python
from backend.database.src.client import DataAPIClient
from backend.database.src.models import Jobs

class AuroraProvider(DatabaseProvider):
    """Aurora Serverless v2 implementation"""

    def __init__(self, cluster_arn: str, secret_arn: str, database: str):
        self.client = DataAPIClient(cluster_arn, secret_arn, database)
        self.jobs = Jobs(self.client)

    async def create_job(
        self,
        user_id: str,
        job_type: str,
        request_payload: Dict[str, Any]
    ) -> str:
        return await self.jobs.create_job(
            clerk_user_id=user_id,
            job_type=job_type,
            request_payload=request_payload
        )

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return await self.jobs.get_job(job_id)

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None
    ):
        await self.jobs.update_status(job_id, status.value, error_message)

    async def store_agent_output(
        self,
        job_id: str,
        agent_name: str,
        output_payload: Dict[str, Any]
    ):
        # Store in agent_results JSONB column
        job = await self.get_job(job_id)
        agent_results = job.get('agent_results', {})
        agent_results[agent_name] = output_payload

        await self.jobs.update_agent_results(job_id, agent_results)

    async def get_agent_output(
        self,
        job_id: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        job = await self.get_job(job_id)
        return job.get('agent_results', {}).get(agent_name)

    async def list_jobs(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        return await self.jobs.list_jobs(user_id, status.value if status else None, limit)
```

**Implementation for DynamoDB (new option):**

```python
import boto3
from boto3.dynamodb.conditions import Key
import uuid

class DynamoDBProvider(DatabaseProvider):
    """DynamoDB implementation for serverless-first architecture"""

    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    async def create_job(
        self,
        user_id: str,
        job_type: str,
        request_payload: Dict[str, Any]
    ) -> str:
        job_id = str(uuid.uuid4())

        item = {
            'PK': f'USER#{user_id}',
            'SK': f'JOB#{job_id}',
            'job_id': job_id,
            'user_id': user_id,
            'job_type': job_type,
            'status': JobStatus.PENDING.value,
            'request_payload': request_payload,
            'agent_results': {},
            'created_at': datetime.utcnow().isoformat()
        }

        self.table.put_item(Item=item)
        return job_id

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        # Query by GSI on job_id
        response = self.table.query(
            IndexName='JobIdIndex',
            KeyConditionExpression=Key('job_id').eq(job_id)
        )

        items = response.get('Items', [])
        return items[0] if items else None

    async def store_agent_output(
        self,
        job_id: str,
        agent_name: str,
        output_payload: Dict[str, Any]
    ):
        job = await self.get_job(job_id)

        self.table.update_item(
            Key={'PK': job['PK'], 'SK': job['SK']},
            UpdateExpression='SET agent_results.#agent = :output',
            ExpressionAttributeNames={'#agent': agent_name},
            ExpressionAttributeValues={':output': output_payload}
        )

    # ... other methods
```

#### 3.2 Flexible Schema Pattern

**Option A: Single JSONB Column (Simple)**

For databases that support JSONB (PostgreSQL, Aurora):

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Single JSONB column for all agent results
    agent_results JSONB DEFAULT '{}'::jsonb,

    request_payload JSONB,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Query example: Get specific agent result
SELECT
    id,
    agent_results->'reporter' as reporter_output,
    agent_results->'charter' as charter_output
FROM jobs
WHERE id = 'job-uuid';

-- Update example: Store agent result
UPDATE jobs
SET agent_results = jsonb_set(
    agent_results,
    '{reporter}',
    '{"report": "Financial analysis..."}'::jsonb
)
WHERE id = 'job-uuid';
```

**Option B: Separate Table (Recommended for Framework)**

More flexible, supports non-JSONB databases:

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    request_payload JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    result_payload JSONB NOT NULL,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(job_id, agent_name)
);

CREATE INDEX idx_agent_results_job_id ON agent_results(job_id);

-- Query example: Get all results for a job
SELECT
    j.*,
    json_object_agg(ar.agent_name, ar.result_payload) as agent_results
FROM jobs j
LEFT JOIN agent_results ar ON ar.job_id = j.id
WHERE j.id = 'job-uuid'
GROUP BY j.id;
```

**Benefits of Separate Table:**
- Works with any database (not just JSONB-capable)
- Easy to add metadata per agent (execution time, version, etc.)
- Can query/analyze agent performance across jobs
- Supports DynamoDB single-table design
- No schema migration when adding new agents

#### 3.3 Database Provider Factory

```python
from typing import Dict, Any
from enum import Enum

class DatabaseType(Enum):
    AURORA = "aurora-serverless-v2"
    RDS_POSTGRES = "rds-postgres"
    DYNAMODB = "dynamodb"

class DatabaseFactory:
    """Factory for creating database providers"""

    @staticmethod
    def create(db_type: DatabaseType, config: Dict[str, Any]) -> DatabaseProvider:
        if db_type == DatabaseType.AURORA:
            return AuroraProvider(
                cluster_arn=config['cluster_arn'],
                secret_arn=config['secret_arn'],
                database=config['database']
            )

        elif db_type == DatabaseType.DYNAMODB:
            return DynamoDBProvider(
                table_name=config['table_name']
            )

        elif db_type == DatabaseType.RDS_POSTGRES:
            return PostgresProvider(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password']
            )

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

# Usage
db_config = load_config("agents.yaml")["infrastructure"]["database"]
db_provider = DatabaseFactory.create(
    DatabaseType(db_config["provider"]),
    db_config["config"]
)
```

---

### Phase 4: Terraform Modularity (Week 2-3)

#### 4.1 Create Reusable Terraform Modules

**Module: agent_lambda**

```hcl
# terraform_modules/agent_lambda/variables.tf

variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "agents" {
  description = "Map of agent configurations"
  type = map(object({
    timeout     = number
    memory      = number
    handler     = string
    env_vars    = map(string)
    s3_key      = string
  }))
}

variable "lambda_role_arn" {
  description = "IAM role ARN for Lambda functions"
  type        = string
}

variable "s3_bucket_id" {
  description = "S3 bucket containing Lambda packages"
  type        = string
}

variable "common_env_vars" {
  description = "Environment variables common to all agents"
  type        = map(string)
  default     = {}
}

# terraform_modules/agent_lambda/main.tf

resource "aws_lambda_function" "agent" {
  for_each = var.agents

  function_name = "${var.project_name}-${each.key}"
  role          = var.lambda_role_arn
  handler       = lookup(each.value, "handler", "lambda_handler.lambda_handler")
  runtime       = "python3.12"

  s3_bucket = var.s3_bucket_id
  s3_key    = each.value.s3_key

  timeout     = each.value.timeout
  memory_size = each.value.memory

  environment {
    variables = merge(
      var.common_env_vars,
      each.value.env_vars
    )
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Project = var.project_name
    Agent   = each.key
  }
}

resource "aws_cloudwatch_log_group" "agent_logs" {
  for_each = var.agents

  name              = "/aws/lambda/${var.project_name}-${each.key}"
  retention_in_days = 7

  tags = {
    Project = var.project_name
    Agent   = each.key
  }
}

# terraform_modules/agent_lambda/outputs.tf

output "lambda_arns" {
  description = "Map of agent names to Lambda ARNs"
  value = {
    for k, v in aws_lambda_function.agent : k => v.arn
  }
}

output "lambda_names" {
  description = "Map of agent names to Lambda function names"
  value = {
    for k, v in aws_lambda_function.agent : k => v.function_name
  }
}
```

**Module: orchestrator**

```hcl
# terraform_modules/orchestrator/variables.tf

variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "orchestrator_lambda_arn" {
  description = "ARN of orchestrator Lambda function"
  type        = string
}

variable "visibility_timeout" {
  description = "SQS visibility timeout in seconds"
  type        = number
  default     = 900
}

# terraform_modules/orchestrator/main.tf

resource "aws_sqs_queue" "jobs" {
  name                       = "${var.project_name}-jobs"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = 86400  # 1 day

  tags = {
    Project = var.project_name
  }
}

resource "aws_sqs_queue" "jobs_dlq" {
  name = "${var.project_name}-jobs-dlq"

  tags = {
    Project = var.project_name
  }
}

resource "aws_sqs_queue_redrive_policy" "jobs" {
  queue_url = aws_sqs_queue.jobs.id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jobs_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.jobs.arn
  function_name    = var.orchestrator_lambda_arn
  batch_size       = 1

  scaling_config {
    maximum_concurrency = 10
  }
}

# terraform_modules/orchestrator/outputs.tf

output "queue_url" {
  value = aws_sqs_queue.jobs.url
}

output "queue_arn" {
  value = aws_sqs_queue.jobs.arn
}

output "dlq_url" {
  value = aws_sqs_queue.jobs_dlq.url
}
```

#### 4.2 Project Template Structure

**Example project using framework modules:**

```hcl
# my_new_project/terraform/main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Load agents configuration from generated file
locals {
  agents_config = jsondecode(file("${path.module}/agents.auto.tfvars.json"))
}

# IAM Role for all Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 bucket for Lambda packages
resource "aws_s3_bucket" "lambda_packages" {
  bucket = "${var.project_name}-lambda-packages"
}

# Deploy all agents using the module
module "agents" {
  source = "../agent_framework/terraform_modules/agent_lambda"

  project_name    = var.project_name
  agents          = local.agents_config.agents
  lambda_role_arn = aws_iam_role.lambda_role.arn
  s3_bucket_id    = aws_s3_bucket.lambda_packages.id

  common_env_vars = {
    DATABASE_URL      = var.database_url
    BEDROCK_MODEL_ID  = var.bedrock_model_id
    BEDROCK_REGION    = var.bedrock_region
    LANGFUSE_HOST     = var.langfuse_host
    LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
    LANGFUSE_SECRET_KEY = var.langfuse_secret_key
  }
}

# Set up orchestration
module "orchestrator" {
  source = "../agent_framework/terraform_modules/orchestrator"

  project_name           = var.project_name
  orchestrator_lambda_arn = module.agents.lambda_arns["planner"]
  visibility_timeout     = 900
}

# Grant orchestrator permission to invoke other agents
resource "aws_lambda_permission" "orchestrator_invoke" {
  for_each = {
    for k, v in module.agents.lambda_arns : k => v
    if k != "planner"
  }

  statement_id  = "AllowOrchestrator-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "lambda.amazonaws.com"
  source_arn    = module.agents.lambda_arns["planner"]
}

# Outputs
output "queue_url" {
  value = module.orchestrator.queue_url
}

output "agent_functions" {
  value = module.agents.lambda_names
}
```

**Generated configuration file (`agents.auto.tfvars.json`):**

This file is auto-generated from `agents.yaml`:

```json
{
  "agents": {
    "planner": {
      "timeout": 900,
      "memory": 2048,
      "handler": "lambda_handler.lambda_handler",
      "s3_key": "planner/planner_lambda.zip",
      "env_vars": {
        "DATA_CLEANER_FUNCTION": "my-project-data_cleaner",
        "ANALYZER_FUNCTION": "my-project-analyzer"
      }
    },
    "data_cleaner": {
      "timeout": 300,
      "memory": 1024,
      "handler": "lambda_handler.lambda_handler",
      "s3_key": "data_cleaner/data_cleaner_lambda.zip",
      "env_vars": {
        "VALIDATION_API_URL": "https://api.example.com/validate"
      }
    },
    "analyzer": {
      "timeout": 600,
      "memory": 2048,
      "handler": "lambda_handler.lambda_handler",
      "s3_key": "analyzer/analyzer_lambda.zip",
      "env_vars": {}
    }
  }
}
```

#### 4.3 Configuration Generation Script

```python
# agent_framework/cli/generate_terraform_config.py

import yaml
import json
from pathlib import Path
from typing import Dict, Any

def load_agents_yaml(yaml_path: str) -> Dict[str, Any]:
    """Load agents.yaml configuration"""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def generate_terraform_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert agents.yaml to Terraform variables format"""

    agents = config.get('agents', {})
    terraform_agents = {}

    for agent_name, agent_config in agents.items():
        runtime = agent_config.get('runtime', {})

        # Build environment variables
        env_vars = {}

        # Add agent-specific environment variables
        for env_var in runtime.get('environment', []):
            # These will be set from terraform.tfvars or common_env_vars
            pass

        # For orchestrator, add function names of workers
        if agent_config.get('type') == 'orchestrator':
            capabilities = agent_config.get('capabilities', {})
            tools = capabilities.get('tools', [])

            for tool in tools:
                if tool.startswith('invoke_'):
                    worker_name = tool.replace('invoke_', '')
                    env_var_name = f"{worker_name.upper()}_FUNCTION"
                    project_name = config.get('project', {}).get('name', 'project')
                    env_vars[env_var_name] = f"{project_name}-{worker_name}"

        terraform_agents[agent_name] = {
            'timeout': runtime.get('timeout', 300),
            'memory': runtime.get('memory', 1024),
            'handler': 'lambda_handler.lambda_handler',
            's3_key': f"{agent_name}/{agent_name}_lambda.zip",
            'env_vars': env_vars
        }

    return {'agents': terraform_agents}

def main():
    """Generate agents.auto.tfvars.json from agents.yaml"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_terraform_config.py <path/to/agents.yaml>")
        sys.exit(1)

    yaml_path = sys.argv[1]
    config = load_agents_yaml(yaml_path)
    terraform_config = generate_terraform_config(config)

    # Write to terraform directory
    output_path = Path(yaml_path).parent / 'terraform' / 'agents.auto.tfvars.json'
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(terraform_config, f, indent=2)

    print(f"Generated Terraform configuration: {output_path}")

if __name__ == '__main__':
    main()
```

---

### Phase 5: Dynamic Orchestration (Week 3)

#### 5.1 Smart Orchestrator Implementation

**Base orchestrator class:**

```python
# agent_framework/core/orchestrator.py

from typing import Dict, Any, List
from dataclasses import dataclass
import asyncio
from agents import Agent, Runner, trace
from agent_framework.core.job_manager import JobManager
from agent_framework.config.loader import ConfigLoader
from agent_framework.infrastructure.database import DatabaseProvider

@dataclass
class ExecutionStep:
    type: str  # "sequential" or "parallel"
    agents: List[str]

class DynamicOrchestrator:
    """
    Smart orchestrator that selects and executes agents dynamically
    based on input data and orchestration rules
    """

    def __init__(
        self,
        config_loader: ConfigLoader,
        job_manager: JobManager,
        db_provider: DatabaseProvider
    ):
        self.config = config_loader
        self.job_manager = job_manager
        self.db = db_provider
        self.rules_engine = config_loader.get_rules_engine()
        self.registry = config_loader.get_agent_registry()

    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Main orchestration method

        1. Load job data
        2. Analyze input to determine execution plan
        3. Execute agents according to plan
        4. Handle errors and retries
        5. Mark job complete
        """
        try:
            # Update job status
            await self.job_manager.start_job(job_id)

            # Load job data
            job = await self.db.get_job(job_id)
            input_data = job['request_payload']

            # Create execution plan
            plan = await self.create_execution_plan(input_data)

            # Execute plan
            results = await self.execute_plan(job_id, plan, input_data)

            # Mark complete
            await self.job_manager.complete_job(job_id, results)

            return {
                'success': True,
                'plan': plan,
                'results': results
            }

        except Exception as e:
            await self.job_manager.fail_job(job_id, str(e))
            raise

    async def create_execution_plan(
        self,
        input_data: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """
        Create execution plan based on orchestration rules

        Rules are evaluated in order, and matching rules contribute to plan
        """
        context = {
            'input': input_data,
            'prev_step': {}
        }

        # Get plan from rules engine
        raw_plan = self.rules_engine.create_plan(context)

        # Convert to ExecutionStep objects
        plan = []
        for step in raw_plan:
            plan.append(ExecutionStep(
                type=step.get('type', 'sequential'),
                agents=step.get('agents', [])
            ))

        return plan

    async def execute_plan(
        self,
        job_id: str,
        plan: List[ExecutionStep],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the orchestration plan"""

        all_results = {}
        context = {'input': input_data}

        for step_idx, step in enumerate(plan):
            print(f"Executing step {step_idx + 1}: {step.type} - {step.agents}")

            if step.type == 'parallel':
                step_results = await self.run_parallel(job_id, step.agents)
            else:  # sequential
                step_results = await self.run_sequential(job_id, step.agents)

            # Merge results
            all_results.update(step_results)

            # Update context for next step
            context['prev_step'] = step_results

            # Check if we should continue (could have conditional logic here)
            if not self.should_continue(step_results):
                print(f"Stopping execution after step {step_idx + 1}")
                break

        return all_results

    async def run_parallel(
        self,
        job_id: str,
        agent_names: List[str]
    ) -> Dict[str, Any]:
        """Run multiple agents in parallel"""

        # Create tasks for all agents
        tasks = [
            self.invoke_agent(job_id, agent_name)
            for agent_name in agent_names
        ]

        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        agent_results = {}
        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                print(f"Agent {agent_name} failed: {result}")
                agent_results[agent_name] = {'error': str(result)}
            else:
                agent_results[agent_name] = result

        return agent_results

    async def run_sequential(
        self,
        job_id: str,
        agent_names: List[str]
    ) -> Dict[str, Any]:
        """Run agents one after another"""

        agent_results = {}

        for agent_name in agent_names:
            try:
                result = await self.invoke_agent(job_id, agent_name)
                agent_results[agent_name] = result
            except Exception as e:
                print(f"Agent {agent_name} failed: {e}")
                agent_results[agent_name] = {'error': str(e)}
                # Could decide to stop or continue here

        return agent_results

    async def invoke_agent(
        self,
        job_id: str,
        agent_name: str
    ) -> Dict[str, Any]:
        """
        Invoke a specific agent

        This can either:
        1. Call Lambda function directly (like Alex does)
        2. Instantiate agent class and run locally
        """
        import boto3
        import json

        # Get Lambda function name from environment or config
        function_name = self.get_agent_function_name(agent_name)

        if function_name:
            # Invoke via Lambda
            lambda_client = boto3.client('lambda')

            payload = {'job_id': job_id}

            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            return result
        else:
            # Run locally (for testing or single-process mode)
            agent_class = self.registry.get_agent(agent_name)
            if not agent_class:
                raise ValueError(f"Agent not found: {agent_name}")

            agent_instance = agent_class(self.db)
            return await agent_instance.run(job_id)

    def get_agent_function_name(self, agent_name: str) -> str:
        """Get Lambda function name for an agent"""
        import os

        # Try environment variable first
        env_var = f"{agent_name.upper()}_FUNCTION"
        function_name = os.getenv(env_var)

        if not function_name:
            # Construct from project name
            project_name = self.config.get_project_name()
            function_name = f"{project_name}-{agent_name}"

        return function_name

    def should_continue(self, step_results: Dict[str, Any]) -> bool:
        """
        Determine if execution should continue based on step results

        Can implement logic like:
        - Stop if any agent failed
        - Stop if confidence below threshold
        - Always continue
        """
        # Simple implementation: continue if no errors
        for result in step_results.values():
            if isinstance(result, dict) and 'error' in result:
                return False

        return True
```

#### 5.2 Condition Evaluation Examples

**Advanced rules in `agents.yaml`:**

```yaml
orchestration:
  strategy: dynamic

  selection_rules:
    # Rule 1: Based on input data type
    - name: financial_workflow
      condition: "input.data_type == 'financial'"
      agents:
        - sequential: [data_validator, financial_analyzer]
        - parallel: [risk_calculator, compliance_checker]
        - sequential: [reporter]

    # Rule 2: Based on data size (adaptive)
    - name: large_dataset_handling
      condition: "input.row_count > 100000"
      agents:
        - sequential: [data_sampler, quick_analyzer]
      else:
        - sequential: [full_analyzer]

    # Rule 3: Based on previous step results
    - name: validation_required
      condition: "prev_step.analyzer.confidence < 0.7"
      agents:
        - sequential: [manual_reviewer, human_validator]

    # Rule 4: Multi-condition logic
    - name: high_priority_financial
      condition: "input.priority == 'high' and input.data_type == 'financial'"
      agents:
        - parallel: [fast_analyzer, risk_calculator]
        - sequential: [urgent_reporter]

    # Rule 5: Always run these at the end
    - name: final_steps
      condition: "always"
      agents:
        - sequential: [aggregator, notifier]
```

**Enhanced rules engine:**

```python
# agent_framework/config/rules_engine.py

from typing import Any, Dict, List
import operator
from dataclasses import dataclass

@dataclass
class Condition:
    """Parsed condition for evaluation"""
    left: str
    op: str
    right: Any

class RulesEngine:
    """Enhanced rules engine with safe expression evaluation"""

    OPERATORS = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '>=': operator.ge,
        '<': operator.lt,
        '<=': operator.le,
        'in': lambda a, b: a in b,
        'not in': lambda a, b: a not in b,
    }

    def __init__(self, rules: List[Dict]):
        self.rules = rules

    def parse_condition(self, condition_str: str) -> Condition:
        """Parse condition string into components"""
        # Handle special cases
        if condition_str == "always":
            return Condition(left="true", op="==", right="true")

        # Parse expression (e.g., "input.data_type == 'financial'")
        for op_str, op_func in self.OPERATORS.items():
            if op_str in condition_str:
                parts = condition_str.split(op_str)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip().strip("'\"")

                    # Convert right side to appropriate type
                    try:
                        right = int(right)
                    except ValueError:
                        try:
                            right = float(right)
                        except ValueError:
                            pass  # Keep as string

                    return Condition(left=left, op=op_str, right=right)

        raise ValueError(f"Could not parse condition: {condition_str}")

    def get_value(self, path: str, context: Dict[str, Any]) -> Any:
        """
        Safely get value from context using dot notation

        Examples:
            path="input.data_type" -> context['input']['data_type']
            path="prev_step.analyzer.confidence" -> context['prev_step']['analyzer']['confidence']
        """
        parts = path.split('.')
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return None
            else:
                return None

        return value

    def evaluate_condition(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """Evaluate a parsed condition against context"""
        try:
            left_value = self.get_value(condition.left, context)

            if left_value is None:
                return False

            op_func = self.OPERATORS.get(condition.op)
            if not op_func:
                return False

            return op_func(left_value, condition.right)

        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False

    def create_plan(self, context: Dict[str, Any]) -> List[Dict]:
        """Create execution plan based on matching rules"""
        plan = []

        for rule in self.rules:
            condition_str = rule.get("condition", "always")

            try:
                condition = self.parse_condition(condition_str)

                if self.evaluate_condition(condition, context):
                    # Add agents from this rule to plan
                    agents_config = rule.get("agents", [])
                    plan.extend(self.parse_agents_config(agents_config))

            except Exception as e:
                print(f"Error processing rule {rule.get('name', 'unknown')}: {e}")

        return plan

    def parse_agents_config(self, agents_config: List) -> List[Dict]:
        """Parse agents configuration into execution steps"""
        steps = []

        for item in agents_config:
            if isinstance(item, str):
                # Simple agent name -> sequential execution
                steps.append({
                    'type': 'sequential',
                    'agents': [item]
                })
            elif isinstance(item, dict):
                # Explicit configuration
                if 'sequential' in item:
                    steps.append({
                        'type': 'sequential',
                        'agents': item['sequential']
                    })
                elif 'parallel' in item:
                    steps.append({
                        'type': 'parallel',
                        'agents': item['parallel']
                    })

        return steps
```

---

### Phase 6: CLI and Scaffolding Tools (Week 3-4)

#### 6.1 Framework CLI

**CLI structure:**

```python
# agent_framework/cli/main.py

import click
from pathlib import Path

@click.group()
def cli():
    """Agent Framework CLI - Build multi-agent systems fast"""
    pass

@cli.command()
@click.argument('project_name')
@click.option('--template', default='basic', help='Project template (basic|financial|analytics)')
@click.option('--database', default='aurora', help='Database provider (aurora|dynamodb|postgres)')
def init(project_name: str, template: str, database: str):
    """Create a new agent framework project"""
    from agent_framework.cli.scaffolding import create_project

    click.echo(f"Creating new project: {project_name}")
    click.echo(f"Template: {template}")
    click.echo(f"Database: {database}")

    project_path = create_project(project_name, template, database)

    click.echo(f"\n✓ Project created at: {project_path}")
    click.echo("\nNext steps:")
    click.echo(f"  cd {project_name}")
    click.echo("  agent-framework add-agent my_agent --type worker")
    click.echo("  agent-framework package --all")
    click.echo("  agent-framework deploy --stage dev")

@cli.command()
@click.argument('agent_name')
@click.option('--type', default='worker', help='Agent type (worker|orchestrator)')
@click.option('--timeout', default=300, help='Lambda timeout in seconds')
@click.option('--memory', default=1024, help='Lambda memory in MB')
def add_agent(agent_name: str, type: str, timeout: int, memory: int):
    """Add a new agent to the current project"""
    from agent_framework.cli.scaffolding import add_agent_to_project

    click.echo(f"Adding new {type} agent: {agent_name}")

    agent_path = add_agent_to_project(
        agent_name=agent_name,
        agent_type=type,
        timeout=timeout,
        memory=memory
    )

    click.echo(f"\n✓ Agent created at: {agent_path}")
    click.echo("\nFiles created:")
    click.echo(f"  {agent_path}/agent.py")
    click.echo(f"  {agent_path}/templates.py")
    click.echo(f"  {agent_path}/lambda_handler.py")
    click.echo(f"  {agent_path}/test_simple.py")
    click.echo("\nAgent added to agents.yaml")
    click.echo("\nNext steps:")
    click.echo(f"  1. Edit {agent_path}/templates.py to define your prompt")
    click.echo(f"  2. Edit {agent_path}/agent.py to add tools or logic")
    click.echo(f"  3. Run: agent-framework test {agent_name}")

@cli.command()
@click.option('--all', is_flag=True, help='Package all agents')
@click.option('--agent', help='Package specific agent')
def package(all: bool, agent: str):
    """Package agents for deployment"""
    from agent_framework.cli.packaging import package_agents

    if all:
        click.echo("Packaging all agents...")
        agents = package_agents()
        click.echo(f"\n✓ Packaged {len(agents)} agents")
        for agent_name in agents:
            click.echo(f"  - {agent_name}")
    elif agent:
        click.echo(f"Packaging agent: {agent}")
        package_agents([agent])
        click.echo(f"\n✓ Packaged {agent}")
    else:
        click.echo("Error: Specify --all or --agent NAME")

@cli.command()
@click.option('--stage', default='dev', help='Deployment stage (dev|prod)')
@click.option('--auto-approve', is_flag=True, help='Skip confirmation')
def deploy(stage: str, auto_approve: bool):
    """Deploy infrastructure with Terraform"""
    from agent_framework.cli.deployment import deploy_infrastructure

    click.echo(f"Deploying to stage: {stage}")

    if not auto_approve:
        click.confirm('This will create AWS resources. Continue?', abort=True)

    deploy_infrastructure(stage, auto_approve)

    click.echo("\n✓ Deployment complete")

@cli.command()
@click.argument('agent_name')
@click.option('--input', help='Input JSON file')
def test(agent_name: str, input: str):
    """Test an agent locally"""
    from agent_framework.cli.testing import test_agent_locally
    import json

    click.echo(f"Testing agent: {agent_name}")

    test_input = {}
    if input:
        with open(input) as f:
            test_input = json.load(f)

    result = test_agent_locally(agent_name, test_input)

    click.echo("\nResult:")
    click.echo(json.dumps(result, indent=2))

@cli.command()
@click.option('--stage', default='dev', help='Stage to destroy')
@click.option('--auto-approve', is_flag=True, help='Skip confirmation')
def destroy(stage: str, auto_approve: bool):
    """Destroy infrastructure"""
    from agent_framework.cli.deployment import destroy_infrastructure

    click.echo(f"⚠️  WARNING: This will destroy all resources in stage: {stage}")

    if not auto_approve:
        click.confirm('Are you sure?', abort=True)

    destroy_infrastructure(stage)

    click.echo("\n✓ Resources destroyed")

if __name__ == '__main__':
    cli()
```

#### 6.2 Code Generation - Agent Scaffolding

**Agent template generator:**

```python
# agent_framework/cli/scaffolding.py

from pathlib import Path
from typing import Dict, Any
import yaml

# Template for agent.py
AGENT_TEMPLATE = '''"""
{agent_name} Agent

Description: TODO: Add description
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from agents import Agent, function_tool, RunContextWrapper
from agent_framework.observability import observe
from agent_framework.infrastructure.database import DatabaseProvider
from .templates import {agent_name_upper}_INSTRUCTIONS

# Optional: Define context if agent uses tools
@dataclass
class {agent_class}Context:
    job_id: str
    db: DatabaseProvider
    # Add other context fields as needed

# Optional: Define tools
@function_tool
async def example_tool(
    wrapper: RunContextWrapper[{agent_class}Context],
    query: str
) -> str:
    """
    Example tool function

    Args:
        wrapper: Context wrapper with job_id and db access
        query: Example query parameter

    Returns:
        Result string
    """
    job_id = wrapper.context.job_id
    db = wrapper.context.db

    # TODO: Implement tool logic

    return "Tool result"

def create_agent(job_id: str, db: DatabaseProvider):
    """
    Create and configure the agent

    Returns:
        Tuple of (model, tools, task, context)
    """
    from agents.litellm import LitellmModel
    import os

    # Get model configuration
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
    bedrock_region = os.getenv("BEDROCK_REGION", "us-east-1")

    # Critical for LiteLLM + Bedrock
    os.environ["AWS_REGION_NAME"] = bedrock_region

    model = LitellmModel(model=f"bedrock/{{model_id}}")

    # Define tools (empty list if no tools)
    tools = [example_tool]

    # Create context
    context = {agent_class}Context(job_id=job_id, db=db)

    # Define task
    task = "TODO: Define the agent's task"

    return model, tools, task, context
'''

# Template for templates.py
TEMPLATES_TEMPLATE = '''"""
Prompt templates for {agent_name} agent
"""

{agent_name_upper}_INSTRUCTIONS = """
You are the {agent_name} agent.

TODO: Write your agent's instructions here.

Guidelines:
- Be specific about what the agent should do
- Include any constraints or requirements
- Specify output format if needed

Example:
Your task is to analyze the input data and provide insights.
Return your analysis in the following format:
- Key findings
- Recommendations
- Confidence score (0-1)
"""
'''

# Template for lambda_handler.py
LAMBDA_HANDLER_TEMPLATE = '''"""
Lambda handler for {agent_name} agent
"""

import json
import os
from typing import Dict, Any
from agents import Agent, Runner, trace
from agent_framework.observability import observe
from agent_framework.infrastructure.database import DatabaseFactory, DatabaseType
from .agent import create_agent, {agent_class}Context
from .templates import {agent_name_upper}_INSTRUCTIONS

def extract_job_id(event: Dict[str, Any]) -> str:
    """Extract job_id from Lambda event"""
    # SQS event
    if 'Records' in event:
        body = json.loads(event['Records'][0]['body'])
        return body['job_id']

    # Direct invocation
    if 'job_id' in event:
        return event['job_id']

    # API Gateway
    if 'body' in event:
        body = json.loads(event['body'])
        return body['job_id']

    raise ValueError("Could not extract job_id from event")

async def run_{agent_name}(job_id: str) -> Dict[str, Any]:
    """Main agent execution function"""

    # Initialize database
    db = DatabaseFactory.create(
        db_type=DatabaseType(os.getenv("DATABASE_TYPE", "aurora-serverless-v2")),
        config={{
            "cluster_arn": os.getenv("AURORA_CLUSTER_ARN"),
            "secret_arn": os.getenv("AURORA_SECRET_ARN"),
            "database": os.getenv("DATABASE_NAME")
        }}
    )

    # Create agent
    model, tools, task, context = create_agent(job_id, db)

    # Run agent
    with trace("{agent_name} Agent"):
        agent = Agent[{agent_class}Context](
            name="{agent_name}",
            instructions={agent_name_upper}_INSTRUCTIONS,
            model=model,
            tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context,
            max_turns=20
        )

        response = result.final_output

    # Store result in database
    await db.store_agent_output(
        job_id=job_id,
        agent_name="{agent_name}",
        output_payload={{"result": response}}
    )

    return {{"success": True, "output": response}}

def lambda_handler(event, context):
    """AWS Lambda handler"""
    import asyncio

    with observe():
        try:
            job_id = extract_job_id(event)

            # Run async function
            result = asyncio.run(run_{agent_name}(job_id))

            return {{
                "statusCode": 200,
                "body": json.dumps(result)
            }}

        except Exception as e:
            print(f"Error in {agent_name} agent: {{e}}")
            return {{
                "statusCode": 500,
                "body": json.dumps({{"error": str(e)}})
            }}
'''

# Template for test_simple.py
TEST_SIMPLE_TEMPLATE = '''"""
Local testing for {agent_name} agent
"""

import asyncio
import os
from .agent import create_agent

# Set test environment variables
os.environ["BEDROCK_MODEL_ID"] = "us.amazon.nova-pro-v1:0"
os.environ["BEDROCK_REGION"] = "us-east-1"
os.environ["DATABASE_TYPE"] = "aurora-serverless-v2"

async def test_{agent_name}():
    """Test agent locally with mock data"""

    # TODO: Set up test data
    job_id = "test-job-123"

    # TODO: Mock database or use test database
    from agent_framework.infrastructure.database import DatabaseFactory, DatabaseType
    db = DatabaseFactory.create(
        db_type=DatabaseType.AURORA,
        config={{
            "cluster_arn": os.getenv("AURORA_CLUSTER_ARN"),
            "secret_arn": os.getenv("AURORA_SECRET_ARN"),
            "database": os.getenv("DATABASE_NAME")
        }}
    )

    # Run agent
    from .lambda_handler import run_{agent_name}
    result = await run_{agent_name}(job_id)

    print("Result:", result)
    assert result["success"], "Agent execution failed"

if __name__ == "__main__":
    asyncio.run(test_{agent_name}())
'''

def create_agent_files(
    project_path: Path,
    agent_name: str,
    agent_type: str
) -> Path:
    """Create all files for a new agent"""

    # Convert agent_name to different formats
    agent_class = ''.join(word.capitalize() for word in agent_name.split('_'))
    agent_name_upper = agent_name.upper()

    # Create agent directory
    agent_path = project_path / "backend" / "agents" / agent_name
    agent_path.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    (agent_path / "__init__.py").write_text("")

    # Create agent.py
    agent_content = AGENT_TEMPLATE.format(
        agent_name=agent_name,
        agent_class=agent_class,
        agent_name_upper=agent_name_upper
    )
    (agent_path / "agent.py").write_text(agent_content)

    # Create templates.py
    templates_content = TEMPLATES_TEMPLATE.format(
        agent_name=agent_name,
        agent_name_upper=agent_name_upper
    )
    (agent_path / "templates.py").write_text(templates_content)

    # Create lambda_handler.py
    handler_content = LAMBDA_HANDLER_TEMPLATE.format(
        agent_name=agent_name,
        agent_class=agent_class,
        agent_name_upper=agent_name_upper
    )
    (agent_path / "lambda_handler.py").write_text(handler_content)

    # Create test_simple.py
    test_content = TEST_SIMPLE_TEMPLATE.format(
        agent_name=agent_name
    )
    (agent_path / "test_simple.py").write_text(test_content)

    # Create pyproject.toml
    pyproject_content = f'''[project]
name = "{agent_name}"
version = "0.1.0"
description = "{agent_name} agent"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.34.0",
    "openai-agents>=0.1.0",
    "litellm>=1.0.0",
]
'''
    (agent_path / "pyproject.toml").write_text(pyproject_content)

    return agent_path

def add_agent_to_project(
    agent_name: str,
    agent_type: str = "worker",
    timeout: int = 300,
    memory: int = 1024
) -> Path:
    """Add a new agent to the current project"""

    project_path = Path.cwd()

    # Create agent files
    agent_path = create_agent_files(project_path, agent_name, agent_type)

    # Update agents.yaml
    yaml_path = project_path / "agents.yaml"

    if yaml_path.exists():
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {'agents': {}, 'orchestration': {'strategy': 'dynamic', 'selection_rules': []}}

    # Add agent to config
    config['agents'][agent_name] = {
        'type': agent_type,
        'description': f'TODO: Add description for {agent_name}',
        'runtime': {
            'timeout': timeout,
            'memory': memory,
            'environment': []
        },
        'capabilities': {
            'tools': [],
            'structured_output': False
        },
        'dependencies': {
            'database': 'read-write',
            'storage': 'optional'
        },
        'outputs': {
            'database_field': f'{agent_name}_result'
        }
    }

    # Write updated config
    with open(yaml_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return agent_path

def create_project(
    project_name: str,
    template: str = 'basic',
    database: str = 'aurora'
) -> Path:
    """Create a new project from template"""

    project_path = Path.cwd() / project_name
    project_path.mkdir(exist_ok=True)

    # Create directory structure
    (project_path / "backend" / "agents").mkdir(parents=True, exist_ok=True)
    (project_path / "terraform").mkdir(exist_ok=True)

    # Create agents.yaml
    agents_config = {
        'project': {
            'name': project_name,
            'version': '1.0.0',
            'region': 'us-east-1'
        },
        'agents': {},
        'orchestration': {
            'strategy': 'dynamic',
            'selection_rules': []
        },
        'infrastructure': {
            'database': {
                'provider': database,
                'config': {}
            },
            'queue': {
                'provider': 'sqs',
                'config': {}
            },
            'storage': {
                'provider': 's3',
                'config': {}
            }
        }
    }

    with open(project_path / "agents.yaml", 'w') as f:
        yaml.dump(agents_config, f, default_flow_style=False)

    # Create README
    readme_content = f"""# {project_name}

Multi-agent system built with Agent Framework

## Getting Started

1. Add agents:
   ```bash
   agent-framework add-agent my_agent --type worker
   ```

2. Configure agents.yaml with your orchestration rules

3. Package and deploy:
   ```bash
   agent-framework package --all
   agent-framework deploy --stage dev
   ```

## Project Structure

- `backend/agents/` - Agent implementations
- `terraform/` - Infrastructure as code
- `agents.yaml` - Agent configuration
"""

    (project_path / "README.md").write_text(readme_content)

    return project_path
```

---

### Phase 7: Documentation and Examples (Week 4)

#### 7.1 Example Projects

**Example 1: Alex-Finance (Migrated)**

```yaml
# alex-finance/agents.yaml

project:
  name: alex-finance
  version: 2.0.0
  region: us-east-1

agents:
  planner:
    type: orchestrator
    description: "Coordinates financial analysis workflow"
    runtime:
      timeout: 900
      memory: 2048
      triggers: [sqs_queue]
    capabilities:
      tools: [invoke_tagger, invoke_reporter, invoke_charter, invoke_retirement]
    dependencies:
      database: read-write
      queue: required
      external_apis: [polygon]

  tagger:
    type: worker
    description: "Classifies financial instruments"
    runtime:
      timeout: 300
      memory: 1024
    capabilities:
      structured_output: true
      output_schema: InstrumentClassification
    outputs:
      database_field: tagger_result

  reporter:
    type: worker
    description: "Generates portfolio analysis reports"
    runtime:
      timeout: 600
      memory: 2048
    capabilities:
      tools: [get_market_insights]
    dependencies:
      storage: required  # S3 Vectors
      external_apis: [sagemaker]
    outputs:
      database_field: report_payload

  charter:
    type: worker
    description: "Creates visualization specifications"
    runtime:
      timeout: 300
      memory: 1024
    outputs:
      database_field: charts_payload

  retirement:
    type: worker
    description: "Calculates retirement projections"
    runtime:
      timeout: 300
      memory: 1024
    outputs:
      database_field: retirement_payload

orchestration:
  strategy: sequential  # Alex uses sequential orchestration
  selection_rules:
    - name: standard_portfolio_analysis
      condition: "always"
      agents:
        - sequential: [tagger]
        - parallel: [reporter, charter, retirement]
```

**Example 2: Sales Analytics (New Domain)**

```yaml
# sales-analytics/agents.yaml

project:
  name: sales-analytics
  version: 1.0.0
  region: us-east-1

agents:
  coordinator:
    type: orchestrator
    description: "Coordinates sales data analysis"
    runtime:
      timeout: 900
      memory: 2048
    capabilities:
      tools: [invoke_data_cleaner, invoke_trend_analyzer, invoke_forecast_agent]

  data_cleaner:
    type: worker
    description: "Cleans and validates sales data"
    runtime:
      timeout: 300
      memory: 1024
    capabilities:
      tools: [validate_schema, remove_outliers]
    outputs:
      database_field: cleaned_data

  trend_analyzer:
    type: worker
    description: "Identifies sales trends and patterns"
    runtime:
      timeout: 600
      memory: 2048
    capabilities:
      tools: [calculate_trends, segment_analysis]
    outputs:
      database_field: trend_analysis

  forecast_agent:
    type: worker
    description: "Forecasts future sales"
    runtime:
      timeout: 600
      memory: 2048
    capabilities:
      tools: [time_series_forecast]
    outputs:
      database_field: forecast_data

  insight_reporter:
    type: worker
    description: "Generates executive summary"
    runtime:
      timeout: 300
      memory: 1024
    outputs:
      database_field: report

orchestration:
  strategy: dynamic
  selection_rules:
    - name: full_analysis
      condition: "input.analysis_type == 'full'"
      agents:
        - sequential: [data_cleaner]
        - parallel: [trend_analyzer, forecast_agent]
        - sequential: [insight_reporter]

    - name: quick_trends
      condition: "input.analysis_type == 'quick'"
      agents:
        - sequential: [data_cleaner, trend_analyzer, insight_reporter]
```

#### 7.2 Migration Guide

**Document: MIGRATION.md**

```markdown
# Migrating Alex to Agent Framework

This guide shows how to migrate the original Alex application to use the new Agent Framework.

## Overview

The migration involves:
1. Extracting agent logic into framework structure
2. Moving to configuration-driven infrastructure
3. Updating database schema
4. No changes to agent logic or prompts

## Step 1: Install Framework

\`\`\`bash
pip install agent-framework
\`\`\`

## Step 2: Create agents.yaml

Create `agents.yaml` in project root (see example above)

## Step 3: Restructure Agent Directories

Move agent files to framework structure:

\`\`\`bash
# Before
backend/planner/
  lambda_handler.py
  agent.py
  templates.py
  observability.py

# After (observability moved to framework)
backend/agents/planner/
  lambda_handler.py
  agent.py
  templates.py
\`\`\`

## Step 4: Update Imports

Replace direct imports with framework imports:

\`\`\`python
# Before
from observability import observe

# After
from agent_framework.observability import observe
\`\`\`

\`\`\`python
# Before
from database.src.client import DataAPIClient

# After
from agent_framework.infrastructure.database import DatabaseFactory
\`\`\`

## Step 5: Update Terraform

Replace individual resource definitions with modules:

\`\`\`hcl
# Before: Individual resources for each agent
resource "aws_lambda_function" "planner" { ... }
resource "aws_lambda_function" "tagger" { ... }
# ... repeated 5 times

# After: Single module with for_each
module "agents" {
  source = "agent_framework/terraform_modules/agent_lambda"
  agents = local.agents_config.agents
  ...
}
\`\`\`

## Step 6: Database Schema Migration

Option 1: Keep existing schema (minimal changes)
Option 2: Migrate to agent_results table (recommended)

\`\`\`sql
-- Create new table
CREATE TABLE agent_results (
  id UUID PRIMARY KEY,
  job_id UUID REFERENCES jobs(id),
  agent_name VARCHAR(100),
  result_payload JSONB,
  created_at TIMESTAMP
);

-- Migrate data
INSERT INTO agent_results (job_id, agent_name, result_payload)
SELECT id, 'reporter', report_payload FROM jobs WHERE report_payload IS NOT NULL;

INSERT INTO agent_results (job_id, agent_name, result_payload)
SELECT id, 'charter', charts_payload FROM jobs WHERE charts_payload IS NOT NULL;

-- etc...
\`\`\`

## Step 7: Deploy

\`\`\`bash
# Generate Terraform config from agents.yaml
agent-framework generate-config

# Package agents
agent-framework package --all

# Deploy
agent-framework deploy --stage dev
\`\`\`

## Comparison: Before vs After

### Lines of Code

| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Terraform | 500 lines | 100 lines | 80% |
| Agent boilerplate | 150 lines × 5 | 50 lines × 5 | 66% |
| Database code | 200 lines | 0 (framework) | 100% |
| Observability | 50 lines × 5 | 0 (framework) | 100% |

### Time to Add New Agent

- **Before**: 2-4 hours (create all files, update Terraform, test)
- **After**: 15 minutes (`agent-framework add-agent name`)

### Configuration Changes

- **Before**: Edit 5-10 files (Terraform, env vars, IAM, etc.)
- **After**: Edit `agents.yaml`, run generate-config

## Benefits

1. **Reduced boilerplate**: 70% less code to maintain
2. **Faster iteration**: Add agents in minutes
3. **Consistency**: All agents follow same patterns
4. **Flexibility**: Easy to swap infrastructure components
5. **Testability**: Built-in testing utilities

## Backwards Compatibility

The migrated version is 100% compatible with existing:
- Frontend code (API unchanged)
- Database data (schema compatible)
- Clerk authentication
- AWS infrastructure
\`\`\`

---

## Key Design Decisions

### ✅ Keep From Alex

1. **OpenAI Agents SDK patterns** - Proven, idiomatic agent implementation
2. **Job-based async processing** - SQS → Orchestrator → Workers pattern
3. **Separation of concerns** - handler/agent/templates structure
4. **Docker-based packaging** - Cross-platform Lambda deployment
5. **LiteLLM + Bedrock** - Flexible LLM provider integration
6. **Database as single source of truth** - Stateless agent execution

### 🔄 Make Flexible

1. **Database backend** - Interface allows Aurora/DynamoDB/Postgres
2. **Agent result storage** - Separate table, not hardcoded columns
3. **Infrastructure components** - Optional, swappable modules
4. **Agent selection** - Rule-based dynamic orchestration
5. **Configuration** - YAML-driven, not hardcoded

### 🆕 Add New Capabilities

1. **Agent registry and discovery** - Runtime agent management
2. **Configuration-driven deployment** - Infrastructure from YAML
3. **Dynamic orchestration rules** - Conditional agent execution
4. **CLI scaffolding tools** - Fast project and agent creation
5. **Multiple project templates** - Different domains out of box
6. **Pluggable components** - Easy to extend and customize

---

## Success Criteria

### Phase 1-2 (Weeks 1-2): Foundation
- [ ] Framework package structure created
- [ ] Core abstractions working (database, queue, storage)
- [ ] Configuration system loading agents.yaml
- [ ] Basic CLI commands (init, add-agent)

### Phase 3-4 (Weeks 2-3): Infrastructure
- [ ] Database abstraction with Aurora + DynamoDB implementations
- [ ] Terraform modules created and tested
- [ ] Agents deploy via module with for_each
- [ ] Configuration generation from YAML working

### Phase 5 (Week 3): Orchestration
- [ ] Dynamic orchestrator implemented
- [ ] Rules engine evaluating conditions
- [ ] Sequential and parallel execution working
- [ ] Orchestrator selects agents based on input

### Phase 6-7 (Weeks 3-4): Tooling & Examples
- [ ] CLI commands complete (package, deploy, test, destroy)
- [ ] Agent scaffolding generates all required files
- [ ] Alex migrated to framework successfully
- [ ] New example project (sales-analytics) deployed
- [ ] Documentation complete

### Final Success Metrics
1. **Speed**: Deploy new multi-agent system in <1 day
2. **Simplicity**: Adding new agent requires only agent.py + templates.py + YAML entry
3. **Flexibility**: Can swap Aurora for DynamoDB with config change only
4. **Intelligence**: Orchestrator selects agents at runtime based on input
5. **Portability**: Framework works for non-financial domains

---

## Migration Path

To ensure a smooth transition:

1. **Keep original Alex intact** - Don't modify existing code
2. **Extract framework alongside** - Build in parallel
3. **Create "Alex v2"** - Rebuild using framework
4. **Compare and validate** - Ensure feature parity
5. **Run both in parallel** - Gradual migration
6. **Archive original** - After validation complete

---

## Next Steps

### For Implementation

1. Start with Phase 1: Create framework package structure
2. Extract database and observability modules from Alex
3. Build configuration system and loader
4. Create first Terraform module (agent_lambda)
5. Test with single agent before building full system

### For Questions/Discussion

- Database strategy: Single JSONB vs separate table?
- Deployment: Support multiple stages (dev/prod)?
- Testing: Unit tests, integration tests, or both?
- Observability: Keep LangFuse or make pluggable?
- Versioning: How to handle framework updates?

---

## Related Documentation

- **Alex Course Guides** - Original implementation in `guides/`
- **OpenAI Agents SDK** - https://github.com/openai/agents-sdk
- **LiteLLM Documentation** - https://docs.litellm.ai/
- **Terraform Best Practices** - https://www.terraform-best-practices.com/

---

*This template plan transforms Alex from a single-purpose financial application into a reusable framework for building any multi-agent system. The goal is to preserve Alex's proven patterns while adding flexibility, configurability, and ease of use.*
