# Testing Quick Reference

## Backend Testing

### Run All Tests
```bash
cd backend
uv run run_all_tests.py
```

### Run Specific Agent
```bash
cd backend
uv run run_all_tests.py --agent reporter
```

### Run Individual Test File
```bash
cd backend/reporter
uv run pytest tests/test_agent.py -v
```

### Run with Coverage
```bash
cd backend/reporter
uv run pytest tests/ --cov=src --cov-report=html
```

## Frontend Testing

### Unit Tests
```bash
cd frontend

# Run once
npm test

# Watch mode
npm test -- --watch

# With coverage
npm test -- --coverage

# Specific test
npm test -- Layout.test.tsx
```

### E2E Tests
```bash
cd frontend

# All tests (headless)
npx playwright test

# Interactive UI
npx playwright test --ui

# Headed (see browser)
npx playwright test --headed

# Specific browser
npx playwright test --project=chromium

# Specific test
npx playwright test portfolio-flow

# Debug mode
npx playwright test --debug
```

## Writing Tests

### Backend Test Template
```python
# backend/myagent/tests/test_myfeature.py
import pytest
from mocks import MockDatabase
from fixtures import SAMPLE_PORTFOLIO
from assertions import assert_valid_portfolio_structure

class TestMyFeature:
    """Test description"""

    def test_something(self, mock_db):
        """Test specific behavior"""
        # Arrange
        portfolio = SAMPLE_PORTFOLIO

        # Act
        result = do_something(portfolio)

        # Assert
        assert result is not None
        assert_valid_portfolio_structure(result)
```

### Frontend Component Test Template
```typescript
// frontend/__tests__/components/MyComponent.test.tsx
import { render, screen, fireEvent } from '@/test-utils'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })

  it('handles interaction', () => {
    const onClick = jest.fn()
    render(<MyComponent onClick={onClick} />)

    fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalled()
  })
})
```

### Frontend Page Test Template
```typescript
// frontend/__tests__/pages/mypage.test.tsx
import { render, screen, waitFor } from '@/test-utils'
import { mockFetch } from '@/test-utils'
import MyPage from '@/pages/mypage'

jest.mock('next/router', () => ({
  useRouter: () => ({ pathname: '/mypage', push: jest.fn() }),
}))

describe('MyPage', () => {
  it('loads data', async () => {
    mockFetch({ data: 'test' })
    render(<MyPage />)

    await waitFor(() => {
      expect(screen.getByText('test')).toBeInTheDocument()
    })
  })
})
```

### E2E Test Template
```typescript
// frontend/e2e/my-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('My Flow', () => {
  test('completes workflow', async ({ page }) => {
    await page.goto('/start')
    await page.click('button:has-text("Next")')
    await expect(page.locator('text=Success')).toBeVisible()
  })
})
```

## Common Patterns

### Mock API Call (Frontend)
```typescript
import { mockFetch } from '@/test-utils'

mockFetch({ accounts: [...] })  // Success
mockFetch({ error: 'Failed' }, false)  // Error
```

### Mock Database (Backend)
```python
from mocks import MockDatabase

db = MockDatabase()
db.setup_test_data()
user = db.users.find_by_clerk_id("test_user_001")
```

### Wait for Async (Frontend)
```typescript
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// Or use findBy
expect(await screen.findByText('Loaded')).toBeInTheDocument()
```

### Async Test (Backend)
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

## Debugging

### Backend - Print Output
```bash
cd backend/reporter
uv run pytest tests/test_agent.py -v -s
```

### Frontend - Specific Test
```bash
cd frontend
npm test -- --testNamePattern="renders correctly"
```

### E2E - Debug Mode
```bash
cd frontend
npx playwright test --debug
```

### E2E - Screenshots
```bash
cd frontend
npx playwright test --screenshot=on
```

## Coverage

### View Backend Coverage
```bash
cd backend/reporter
uv run pytest tests/ --cov=src --cov-report=html
open coverage_html/index.html
```

### View Frontend Coverage
```bash
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

## CI/CD

### Local CI Simulation
```bash
# Backend (all agents)
cd backend && uv run run_all_tests.py

# Frontend (all tests)
cd frontend
npm test -- --coverage --maxWorkers=2
npx playwright install chromium
npx playwright test --project=chromium
```

### Check CI Status
- Go to GitHub repository
- Click "Actions" tab
- View latest workflow run
- Check individual job logs

## Useful Commands

### Install Dependencies
```bash
# Backend
cd backend/reporter
uv add --optional test pytest pytest-asyncio pytest-cov

# Frontend
cd frontend
npm install
npx playwright install
```

### Clean Up
```bash
# Backend
cd backend/reporter
rm -rf .pytest_cache coverage_html

# Frontend
cd frontend
rm -rf coverage playwright-report
```

### Update Snapshots
```bash
# Frontend
cd frontend
npm test -- -u
```

## Key Files

### Backend
- `backend/tests_common/` - Shared utilities
- `backend/run_all_tests.py` - Test runner
- `backend/*/tests/conftest.py` - Test fixtures
- `backend/README_TESTING.md` - Full guide

### Frontend
- `frontend/__tests__/` - Unit tests
- `frontend/e2e/` - E2E tests
- `frontend/test-utils/` - Utilities
- `frontend/__mocks__/` - Mocks
- `frontend/jest.config.js` - Jest config
- `frontend/playwright.config.ts` - Playwright config
- `frontend/README_TESTING.md` - Full guide

## Help

For detailed information, see:
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Complete overview
- [backend/README_TESTING.md](backend/README_TESTING.md) - Backend details
- [frontend/README_TESTING.md](frontend/README_TESTING.md) - Frontend details
- [TESTING_IMPLEMENTATION_SUMMARY.md](TESTING_IMPLEMENTATION_SUMMARY.md) - Implementation details
