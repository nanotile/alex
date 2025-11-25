# Backend Testing Guide

This guide explains how to run and write tests for the Alex backend agents.

## Quick Start

### Run All Tests

```bash
cd backend
uv run run_all_tests.py
```

### Run Tests for Specific Agent

```bash
cd backend
uv run run_all_tests.py --agent reporter
```

### Run Tests Without Coverage (Faster)

```bash
cd backend
uv run run_all_tests.py --fast
```

### Run Tests with Verbose Output

```bash
cd backend
uv run run_all_tests.py -v
```

## Test Structure

Each agent directory has the following test structure:

```
backend/
├── [agent_name]/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest fixtures
│   │   ├── test_agent.py         # Agent logic tests
│   │   ├── test_lambda_handler.py # Lambda handler tests
│   │   └── test_*.py             # Additional test files
│   ├── test_simple.py            # Quick local test
│   └── test_full.py              # AWS integration test
```

## Test Categories

### 1. Unit Tests (`tests/test_agent.py`)

Test agent logic, helper functions, and calculations without AWS dependencies.

**Example:**
```python
def test_calculate_portfolio_metrics(sample_portfolio):
    metrics = calculate_portfolio_metrics(sample_portfolio)
    assert metrics['total_value'] > 0
    assert metrics['num_accounts'] == 2
```

### 2. Lambda Handler Tests (`tests/test_lambda_handler.py`)

Test Lambda entry points with mocked AWS services.

**Example:**
```python
@patch('lambda_handler.Database')
def test_successful_invocation(mock_db):
    event = {"job_id": "test_job"}
    result = lambda_handler(event, None)
    assert result['statusCode'] == 200
```

### 3. Simple Tests (`test_simple.py`)

Quick local tests with `MOCK_LAMBDAS=true` for rapid development.

**Usage:**
```bash
cd backend/reporter
uv run test_simple.py
```

### 4. Full Integration Tests (`test_full.py`)

End-to-end tests with actual AWS resources (requires deployed infrastructure).

**Usage:**
```bash
cd backend/reporter
uv run test_full.py
```

## Common Test Utilities

The `backend/tests_common/` directory provides shared testing utilities:

### Mocks (`mocks.py`)

- `MockDatabase` - Mock Aurora Data API
- `MockLiteLLM` - Mock Bedrock/LiteLLM
- `MockLambda` - Mock Lambda invocations
- `MockSQS` - Mock SQS operations

**Example:**
```python
from mocks import MockDatabase

def test_with_mock_db():
    db = MockDatabase()
    db.setup_test_data()
    user = db.users.find_by_clerk_id("test_user_001")
    assert user is not None
```

### Fixtures (`fixtures.py`)

Pre-defined test data:

- `SAMPLE_PORTFOLIO` - Complete portfolio structure
- `SAMPLE_USER_PREFS` - User preferences
- `SAMPLE_INSTRUMENTS` - ETF/stock data
- `SAMPLE_JOB` - Job data

**Example:**
```python
from fixtures import SAMPLE_PORTFOLIO

def test_portfolio_analysis():
    metrics = analyze(SAMPLE_PORTFOLIO)
    assert metrics['total_value'] > 0
```

### Assertions (`assertions.py`)

Custom assertions for common validations:

- `assert_valid_portfolio_structure(portfolio)`
- `assert_valid_job_structure(job)`
- `assert_agent_response_valid(response)`
- `assert_lambda_response_valid(response)`

## Writing New Tests

### 1. Create Test File

```python
# backend/myagent/tests/test_myfeature.py

import pytest
from unittest.mock import Mock, patch

class TestMyFeature:
    """Test description"""

    def test_something(self, mock_db):
        """Test specific behavior"""
        result = do_something()
        assert result is not None
```

### 2. Add Fixtures (if needed)

```python
# backend/myagent/tests/conftest.py

@pytest.fixture
def my_fixture():
    """Provide test data"""
    return {"key": "value"}
```

### 3. Run Tests

```bash
cd backend/myagent
uv run pytest tests/ -v
```

## Test Coverage

### View Coverage Report

After running tests with coverage:

```bash
cd backend/reporter
open coverage_html/index.html  # macOS
xdg-open coverage_html/index.html  # Linux
```

### Coverage Goals

- **Unit tests**: 80%+ coverage
- **Integration tests**: Cover critical paths
- **Lambda handlers**: 100% coverage

## Continuous Integration

Tests run automatically on GitHub Actions for every push/PR.

See `.github/workflows/test.yml` for configuration.

## Troubleshooting

### Import Errors

If you get import errors, ensure you're in the agent directory:

```bash
cd backend/reporter
uv run pytest tests/
```

### Missing Dependencies

Install test dependencies:

```bash
cd backend/reporter
uv add --optional test pytest pytest-asyncio pytest-cov
```

### Async Test Warnings

Mark async tests with decorator:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

## Best Practices

1. **Test behavior, not implementation** - Test what the code does, not how
2. **Keep tests fast** - Use mocks to avoid slow I/O operations
3. **Use descriptive names** - `test_calculate_metrics_with_empty_portfolio()`
4. **One assertion per test** - Makes failures easier to diagnose
5. **Arrange-Act-Assert** - Structure tests clearly
6. **Test edge cases** - Empty inputs, null values, errors
7. **Mock external dependencies** - Don't call actual AWS services in unit tests

## Example Test

```python
import pytest
from mocks import MockDatabase
from fixtures import SAMPLE_PORTFOLIO
from assertions import assert_valid_portfolio_structure

class TestPortfolioAnalysis:
    """Test portfolio analysis features"""

    def test_analyze_portfolio_success(self, mock_db):
        """Test successful portfolio analysis"""
        # Arrange
        portfolio = SAMPLE_PORTFOLIO.copy()
        assert_valid_portfolio_structure(portfolio)

        # Act
        result = analyze_portfolio(portfolio)

        # Assert
        assert result is not None
        assert 'total_value' in result
        assert result['total_value'] > 0

    def test_analyze_empty_portfolio(self):
        """Test handling empty portfolio"""
        # Arrange
        portfolio = {"accounts": []}

        # Act
        result = analyze_portfolio(portfolio)

        # Assert
        assert result['total_value'] == 0
        assert result['num_accounts'] == 0
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Moto (AWS mocking)](https://docs.getmoto.org/)
