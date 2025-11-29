# Claude Code System Requirements - Alex Project

## Project Overview

**Alex** (Agentic Learning Equities eXplainer) is a multi-cloud, production-grade AI agent platform for financial portfolio analysis. This document defines the system requirements and development standards for working with Claude Code on this project.

---

## PROGRAMMING SYSTEM REQUIREMENTS

### Code & Structure
- **Python 3.12** with **uv** package management (NOT conda, NOT pip).
- **AWS cloud architecture**: Production-grade AWS deployment.
- **Complete runnable system** delivered each time.
- **Incremental development** with proper git commits.
- **All code must be placed in the correct directory** per the project structure (see KB_FILE_STRUCTURE.md).
- **NextJS React** for frontend (Pages Router, NOT App Router).
- **Terraform** for infrastructure as code.
- **Docker** for containerization (linux/amd64 platform).

### Package Management (CRITICAL)
- **ALWAYS use `uv`** for Python dependencies:
  - `uv add <package>` to add dependencies
  - `uv run <script.py>` to run Python scripts
  - `uv run pytest` to run tests
- **NEVER use:**
  - `pip install`
  - `python script.py` (use `uv run script.py`)
  - `python -m module` (use `uv run -m module`)
  - `conda` environments
- **Each agent directory** is its own uv project with `pyproject.toml`.
- **Nested uv projects** are acceptable (e.g., backend/ has pyproject.toml, backend/planner/ also has one).

### File Naming & Versioning
- **Agent code** follows standard pattern:
  - `lambda_handler.py` or `main.py` (entry point)
  - `agent.py` (agent logic using OpenAI Agents SDK)
  - `templates.py` (prompt templates)
  - `test_simple.py` (local mock tests)
  - `test_full.py` (deployment tests)
  - `package_docker.py` (Docker packaging for Lambda)
- **Version control** via git commits, not file naming.
- **No version numbers in filenames** (use git history instead).

### Python File Header Format (Simplified)

For agent files, include a docstring at the top:

```python
"""
Agent Name: [Planner/Tagger/Reporter/etc.]
Purpose: [Brief description]
Cloud: AWS Lambda
Model: AWS Bedrock Nova Pro
Framework: OpenAI Agents SDK
"""
```

**Optional sections for complex modules:**
- Database schema references
- API endpoints
- External dependencies

### AWS Deployment Architecture

**AWS Services:**
- Lambda functions for agents
- Aurora Serverless v2 for database
- S3 Vectors for embeddings
- SageMaker for embedding endpoint
- Bedrock Nova Pro for LLM
- CloudWatch for monitoring

**Application Framework:**
- OpenAI Agents SDK for all agents
- LiteLLM for AWS Bedrock interface
- Clerk for authentication
- NextJS for frontend

---

## TESTING REQUIREMENTS

### Backend Testing
- **ALWAYS provide both test files:**
  - `test_simple.py`: Mock mode with `MOCK_LAMBDAS=true`
  - `test_full.py`: Real AWS deployment tests
- **Use shared utilities:**
  - Import from `backend/tests_common/`
  - Fixtures, mocks, assertions
- **Coverage:** Maintain >80% code coverage
- **Run tests:** `uv run pytest`

### Frontend Testing
- **Unit tests:** Jest + React Testing Library
- **E2E tests:** Playwright for critical workflows
- **Test files in:**
  - `frontend/__tests__/` for unit tests
  - `frontend/e2e/` for E2E tests
- **Run tests:** `npm test` or `npm run test:e2e`

### Test-Driven Development
1. Write `test_simple.py` first (TDD approach)
2. Implement agent logic
3. Run local tests: `uv run pytest test_simple.py`
4. Deploy to cloud
5. Run deployment tests: `uv run pytest test_full.py`

---

## AGENT DEVELOPMENT STANDARDS

### OpenAI Agents SDK Patterns

**Standard Agent Creation:**
```python
from agents import Agent, Runner, trace
from litellm_model import LitellmModel

model = LitellmModel(model=f"bedrock/{model_id}")

with trace("Agent Name"):
    agent = Agent(
        name="Agent Name",
        instructions=AGENT_INSTRUCTIONS,
        model=model,
        tools=tools  # OR structured_outputs (NOT both)
    )

    result = await Runner.run(
        agent,
        input=task,
        max_turns=20
    )

    response = result.final_output
```

**Important:**
- **LiteLLM + Bedrock:** Requires `os.environ["AWS_REGION_NAME"] = region`
- **Structured outputs OR tools:** Cannot use both on same agent
- **Context passing:** Use `Agent[ContextType]` and `RunContextWrapper[ContextType]` for tools that need user context

### Database Patterns

**AWS Aurora (Data API):**
```python
from database import DatabaseClient

db = DatabaseClient(cluster_arn, secret_arn, database_name)
results = await db.execute_sql(query, parameters)
```


---

## INFRASTRUCTURE REQUIREMENTS

### Terraform Standards
- **Independent directories:** Each terraform module is standalone
- **Local state files:** `terraform.tfstate` (NOT remote S3 state)
- **Required files:**
  - `main.tf` (resource definitions)
  - `variables.tf` (input variables)
  - `outputs.tf` (output values)
  - `terraform.tfvars.example` (example configuration)
  - `terraform.tfvars` (actual config, gitignored)
- **Deployment order:** 2→3→4→5→6→7→8

### Docker Requirements
- **Platform:** linux/amd64 (required for Lambda)
- **Build command:** `docker buildx build --platform linux/amd64`
- **Packaging:** Use `package_docker.py` scripts in agent directories
- **Docker must be running:** Before running package scripts

---

## COST MANAGEMENT

### AWS Cost Optimization
- **Aurora Serverless v2:** Biggest cost - destroy when not in use
- **SageMaker Serverless:** Pay per invocation
- **Lambda:** Pay per execution
- **S3 Vectors:** 90% cheaper than OpenSearch

### Cleanup Commands
```bash
# Destroy in reverse order
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy  # Biggest savings
# ... continue in reverse order
```

---

## DOCUMENTATION REQUIREMENTS

### Code Documentation
- **Docstrings:** For all public functions and classes
- **Type hints:** Use Python type annotations
- **Comments:** Only where logic is non-obvious
- **README files:** In each major directory

### Project Documentation
- **CLAUDE.md:** AI assistant instructions (this file's companion)
- **KB_FILE_STRUCTURE.md:** Complete project structure
- **TESTING_*.md:** Testing guides and references
- **README.md:** Project overview with diagrams

### Git Workflow
- **Commits:** Clear, descriptive messages
- **Branches:** Feature branches for new work
- **Main branch:** `main` (default for PRs)
- **Current branch:** Check `git status` before commits
- **No force push:** To main/master

---

## ERROR HANDLING & DEBUGGING

### Common Issues

**1. Docker Not Running**
- Symptom: `package_docker.py` fails
- Fix: Start Docker Desktop

**2. AWS Region Mismatches**
- Symptom: Bedrock access denied
- Fix: Set `AWS_REGION_NAME` environment variable
- Check: Model access granted in Bedrock console

**3. Terraform Variables Missing**
- Symptom: Resources fail to create
- Fix: Copy `terraform.tfvars.example` to `terraform.tfvars`
- Fill in all required values

**4. Lambda Errors**
- Check: CloudWatch logs
- Verify: Environment variables set correctly
- Test: Locally with `test_simple.py` first

### Debugging Process
1. **Reproduce locally** with `test_simple.py`
2. **Check logs:** CloudWatch
3. **Verify config:** Environment variables, tfvars
4. **Test incrementally:** One change at a time
5. **Check permissions:** IAM roles and policies

---

## DEVELOPMENT WORKFLOW

### Standard Development Cycle

1. **Read documentation:**
   - CLAUDE.md for project context
   - KB_FILE_STRUCTURE.md for structure
   - Relevant guide (guides/X_*.md)

2. **Plan implementation:**
   - Use TodoWrite tool for tracking
   - Break down into small tasks
   - One change at a time

3. **Write tests first:**
   - Create `test_simple.py`
   - Define expected behavior
   - Run tests (should fail initially)

4. **Implement code:**
   - Follow existing patterns
   - Use shared utilities
   - Keep it simple (no over-engineering)

5. **Test locally:**
   - `uv run pytest test_simple.py`
   - Fix issues iteratively
   - Verify all tests pass

6. **Deploy to cloud:**
   - Package with `package_docker.py`
   - Apply terraform changes
   - Verify deployment

7. **Test deployment:**
   - `uv run pytest test_full.py`
   - Check CloudWatch logs
   - Validate end-to-end

8. **Commit changes:**
   - Clear commit message
   - Include all related files
   - Push to feature branch

---

## SECURITY & BEST PRACTICES

### Security
- **Never commit secrets:** Use `.env` files (gitignored)
- **IAM least privilege:** Only required permissions
- **Secrets Manager:** For database credentials
- **API keys:** Environment variables only
- **Input validation:** At system boundaries

### Code Quality
- **No over-engineering:** Simplest solution that works
- **DRY principle:** Use shared utilities
- **Single responsibility:** One function, one purpose
- **Consistent style:** Follow existing patterns
- **No premature optimization:** Profile first

### Agent Best Practices
- **Clear prompts:** In `templates.py`
- **Error handling:** Graceful failures
- **Logging:** Use trace() for observability
- **Token limits:** Respect context windows
- **Retry logic:** For transient failures

---

## CROSS-PLATFORM COMPATIBILITY

### Platform Considerations
- **Windows, Mac, Linux:** All supported
- **Use Python scripts:** NOT platform-specific shell scripts
- **Path handling:** Use `pathlib` for cross-platform paths
- **Line endings:** Git handles automatically
- **Docker Desktop:** Required on all platforms

### Tool Requirements
- **uv:** Python package manager
- **Terraform:** Infrastructure as code
- **Docker:** Container runtime
- **Git:** Version control
- **Node.js/npm:** Frontend development
- **AWS CLI:** AWS deployments

---

## CONTINUOUS IMPROVEMENT

### Regular Checks
- **Update dependencies:** `uv lock --upgrade`
- **Run full test suite:** Before major changes
- **Check AWS costs:** Billing dashboard weekly
- **Update documentation:** When structure changes
- **Review logs:** For optimization opportunities

### Performance Optimization
- **Profile before optimizing:** Don't guess
- **Cache where appropriate:** Use cacheLife, cacheTag
- **Batch operations:** Reduce API calls
- **Async/await:** For concurrent operations
- **Monitor cold starts:** Lambda warmup

---

## SUPPORT & RESOURCES

### Documentation References
- **OpenAI Agents SDK:** Latest idiomatic patterns
- **AWS Bedrock:** Nova Pro model documentation
- **LiteLLM:** Universal LLM interface docs
- **Terraform:** AWS provider docs

### Getting Help
- **Check guides first:** `guides/` directory
- **Review examples:** Existing agent implementations
- **Check logs:** CloudWatch
- **Ask specific questions:** Include error messages and context
- **Search codebase:** Use Grep tool for patterns

---

*Last Updated: November 2025*
*Project: Alex - AWS AI Agent Platform*
*Framework: OpenAI Agents SDK*
*Cloud: AWS*
