# Alex Testing Guide

Complete testing framework for the Alex financial planning platform.

## Overview

Alex uses a comprehensive testing strategy covering:

- **Backend Unit Tests** - Test agent logic, calculations, and database operations
- **Backend Integration Tests** - Test Lambda handlers and AWS service interactions
- **Frontend Unit Tests** - Test React components and pages
- **Frontend E2E Tests** - Test complete user workflows with Playwright
- **CI/CD Integration** - Automated testing on GitHub Actions

## Quick Start

### Backend Tests

```bash
# Run all backend tests
cd backend
uv run run_all_tests.py

# Run tests for specific agent
cd backend
uv run run_all_tests.py --agent reporter

# Fast mode (skip coverage)
cd backend
uv run run_all_tests.py --fast
```

### Frontend Tests

```bash
# Run unit tests
cd frontend
npm test

# Run E2E tests
cd frontend
npx playwright test

# Run both with coverage
cd frontend
npm test -- --coverage
npx playwright test
```

## Project Structure

```
alex/
├── backend/
│   ├── tests_common/          # Shared test utilities
│   │   ├── mocks.py           # Mock AWS services
│   │   ├── fixtures.py        # Test data
│   │   └── assertions.py      # Custom assertions
│   ├── database/tests/        # Database layer tests
│   ├── planner/tests/         # Planner agent tests
│   ├── reporter/tests/        # Reporter agent tests
│   ├── tagger/tests/          # Tagger agent tests
│   ├── charter/tests/         # Charter agent tests
│   ├── retirement/tests/      # Retirement agent tests
│   ├── run_all_tests.py       # Test runner
│   └── README_TESTING.md      # Backend testing guide
│
├── frontend/
│   ├── __tests__/             # Unit/integration tests
│   │   ├── components/        # Component tests
│   │   ├── pages/            # Page tests
│   │   └── lib/              # Utility tests
│   ├── __mocks__/            # Module mocks
│   ├── e2e/                  # Playwright E2E tests
│   ├── test-utils/           # Testing utilities
│   ├── jest.config.js        # Jest configuration
│   ├── playwright.config.ts  # Playwright configuration
│   └── README_TESTING.md     # Frontend testing guide
│
└── .github/workflows/
    └── test.yml              # CI/CD workflow
```

## Testing Strategy

### 1. Backend Testing (Python + pytest)

**Test Pyramid:**
- **Unit Tests** (70%) - Pure functions, calculations, business logic
- **Integration Tests** (20%) - Lambda handlers, database operations
- **E2E Tests** (10%) - Full AWS deployment tests

**Key Features:**
- Mock AWS services (Lambda, SQS, Aurora)
- Mock LLM responses (Bedrock/LiteLLM)
- Shared test utilities in `tests_common/`
- Coverage reporting with pytest-cov

**Example:**
```python
from mocks import MockDatabase
from fixtures import SAMPLE_PORTFOLIO
from assertions import assert_valid_portfolio_structure

def test_portfolio_analysis(mock_db):
    portfolio = SAMPLE_PORTFOLIO
    assert_valid_portfolio_structure(portfolio)

    metrics = calculate_metrics(portfolio)
    assert metrics['total_value'] > 0
```

### 2. Frontend Testing (Jest + React Testing Library)

**Test Pyramid:**
- **Component Tests** (60%) - Individual UI components
- **Page Tests** (30%) - Full page rendering and interactions
- **E2E Tests** (10%) - Complete user workflows

**Key Features:**
- Mock Clerk authentication
- Mock API responses
- Mock chart libraries (Recharts)
- Custom render with providers

**Example:**
```typescript
import { render, screen, waitFor } from '@/test-utils'
import { mockFetch } from '@/test-utils'
import Dashboard from '@/pages/dashboard'

test('displays portfolio data', async () => {
  mockFetch({ accounts: [...] })
  render(<Dashboard />)

  await waitFor(() => {
    expect(screen.getByText(/portfolio/i)).toBeInTheDocument()
  })
})
```

### 3. E2E Testing (Playwright)

**Test Scenarios:**
- User authentication flow
- Portfolio analysis workflow
- Navigation between pages
- Responsive design
- Error handling

**Example:**
```typescript
test('complete analysis workflow', async ({ page }) => {
  await page.goto('/dashboard')
  await page.click('button:has-text("Request Analysis")')

  await expect(page.locator('text=/completed/i')).toBeVisible({
    timeout: 180000
  })

  await expect(page.locator('.portfolio-report')).toBeVisible()
})
```

## Coverage Goals

### Backend
- **Overall**: 70%+
- **Business Logic**: 80%+
- **Lambda Handlers**: 100%

### Frontend
- **Overall**: 70%+
- **Components**: 80%+
- **Pages**: 70%+

## Continuous Integration

Tests run automatically on GitHub Actions:

**Triggers:**
- Every push to `main` or `develop`
- Every pull request

**Jobs:**
1. **Backend Tests** - Matrix of all 6 agents
2. **Frontend Unit Tests** - Jest with coverage
3. **Frontend E2E Tests** - Playwright with Chromium
4. **Lint & Type Check** - ESLint and TypeScript

**Results:**
- Coverage reports uploaded to Codecov
- Playwright reports saved as artifacts
- PR status checks require all tests to pass

## Running Tests Locally

### Full Test Suite

```bash
# Backend
cd backend && uv run run_all_tests.py

# Frontend
cd frontend
npm test -- --coverage
npx playwright test
```

### Development Workflow

```bash
# Backend - watch mode for specific agent
cd backend/reporter
uv run pytest tests/ --watch

# Frontend - watch mode
cd frontend
npm test -- --watch

# Frontend - E2E with UI
cd frontend
npx playwright test --ui
```

### Pre-Commit

```bash
# Run before committing
cd backend && uv run run_all_tests.py --fast
cd frontend && npm test
```

## Common Tasks

### Add New Backend Test

```bash
cd backend/myagent/tests
# Create test_myfeature.py
# Use fixtures from tests_common/
```

### Add New Frontend Test

```bash
cd frontend/__tests__/components
# Create MyComponent.test.tsx
# Use utilities from test-utils/
```

### Debug Failing Test

```bash
# Backend - verbose mode
cd backend/reporter
uv run pytest tests/test_agent.py -v -s

# Frontend - specific test
cd frontend
npm test -- MyComponent.test.tsx

# E2E - headed mode
cd frontend
npx playwright test --headed --debug
```

### Update Coverage Thresholds

**Backend:**
```python
# backend/database/pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov-fail-under=70"
```

**Frontend:**
```javascript
// frontend/jest.config.js
coverageThreshold: {
  global: {
    branches: 70,
    functions: 70,
    lines: 70,
    statements: 70,
  },
}
```

## Best Practices

### 1. Test Behavior, Not Implementation

Focus on what the code does, not how it does it.

### 2. Use Descriptive Test Names

```python
# Good
def test_calculate_metrics_returns_zero_for_empty_portfolio():
    ...

# Bad
def test_metrics():
    ...
```

### 3. Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange
    portfolio = create_test_portfolio()

    # Act
    result = analyze(portfolio)

    # Assert
    assert result['total_value'] > 0
```

### 4. Mock External Dependencies

Never make real API calls or database queries in unit tests.

### 5. Keep Tests Fast

- Use mocks to avoid I/O
- Run expensive tests separately
- Parallel execution when possible

### 6. Test Edge Cases

- Empty inputs
- Null values
- Error conditions
- Boundary values

## Troubleshooting

### Backend Tests Fail to Import

```bash
# Ensure you're in the agent directory
cd backend/reporter
uv run pytest tests/
```

### Frontend Tests Timeout

```typescript
// Increase timeout in test
await waitFor(() => { ... }, { timeout: 10000 })
```

### Playwright Browser Not Installed

```bash
cd frontend
npx playwright install
```

### Coverage Not Generated

```bash
# Backend
cd backend/reporter
uv run pytest tests/ --cov=src --cov-report=html

# Frontend
cd frontend
npm test -- --coverage
```

## Resources

- [Backend Testing Guide](backend/README_TESTING.md)
- [Frontend Testing Guide](frontend/README_TESTING.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)

## Getting Help

If you encounter issues with the testing framework:

1. Check the relevant README (backend/frontend)
2. Review example tests in `__tests__/` or `tests/`
3. Check CI logs in GitHub Actions
4. Consult the documentation links above

---

**Remember:** Good tests are investments in code quality and developer productivity. Write tests that give you confidence to refactor and ship quickly!
