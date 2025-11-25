# Frontend Testing Guide

This guide explains how to run and write tests for the Alex frontend application.

## Quick Start

### Install Dependencies

```bash
cd frontend
npm install
```

### Run All Unit Tests

```bash
npm test
```

### Run Tests in Watch Mode

```bash
npm test -- --watch
```

### Run Tests with Coverage

```bash
npm test -- --coverage
```

### Run E2E Tests

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npx playwright test

# Run E2E tests with UI
npx playwright test --ui

# Run specific browser
npx playwright test --project=chromium
```

## Test Structure

```
frontend/
├── __tests__/              # Unit and integration tests
│   ├── components/         # Component tests
│   ├── pages/             # Page tests
│   └── lib/               # Utility/API tests
├── __mocks__/             # Module mocks
│   ├── @clerk/nextjs.tsx  # Mock Clerk auth
│   └── recharts.tsx       # Mock charts
├── e2e/                   # E2E tests with Playwright
│   ├── auth.setup.ts      # Auth setup
│   ├── portfolio-flow.spec.ts
│   ├── navigation.spec.ts
│   └── responsive.spec.ts
├── test-utils/            # Testing utilities
│   ├── index.tsx          # Custom render
│   └── mockData.ts        # Mock data
├── jest.config.js         # Jest configuration
├── jest.setup.js          # Jest setup
└── playwright.config.ts   # Playwright configuration
```

## Writing Tests

### Component Tests

```typescript
// __tests__/components/MyComponent.test.tsx
import { render, screen } from '@/test-utils'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const onClickMock = jest.fn()
    render(<MyComponent onClick={onClickMock} />)

    const button = screen.getByRole('button')
    await button.click()

    expect(onClickMock).toHaveBeenCalled()
  })
})
```

### Page Tests

```typescript
// __tests__/pages/mypage.test.tsx
import { render, screen, waitFor } from '@/test-utils'
import { mockFetch } from '@/test-utils'
import { mockPortfolioData } from '@/test-utils/mockData'
import MyPage from '@/pages/mypage'

// Mock router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/mypage',
    push: jest.fn(),
  }),
}))

describe('MyPage', () => {
  beforeEach(() => {
    mockFetch(mockPortfolioData)
  })

  it('loads and displays data', async () => {
    render(<MyPage />)

    await waitFor(() => {
      expect(screen.getByText(/portfolio/i)).toBeInTheDocument()
    })
  })
})
```

### E2E Tests

```typescript
// e2e/my-feature.spec.ts
import { test, expect } from '@playwright/test'

test.describe('My Feature', () => {
  test('complete user flow', async ({ page }) => {
    await page.goto('/dashboard')

    // Interact with the page
    await page.click('button:has-text("Start")')

    // Assert results
    await expect(page.locator('text=Success')).toBeVisible()
  })
})
```

## Test Utilities

### Custom Render

```typescript
import { render } from '@/test-utils'

// Wraps components with necessary providers (Clerk, etc.)
render(<MyComponent />)
```

### Mock Fetch

```typescript
import { mockFetch } from '@/test-utils'
import { mockPortfolioData } from '@/test-utils/mockData'

// Mock successful API call
mockFetch(mockPortfolioData)

// Mock API error
mockFetch({ error: 'Failed' }, false)
```

### Mock Data

```typescript
import {
  mockUser,
  mockPortfolioData,
  mockCompletedAnalysis,
  mockAccounts,
} from '@/test-utils/mockData'

// Use in tests
test('displays portfolio', () => {
  mockFetch(mockPortfolioData)
  // ... rest of test
})
```

## Mocking

### Mock Clerk Authentication

Already mocked in `__mocks__/@clerk/nextjs.tsx`. All tests run with a signed-in user.

### Mock API Calls

```typescript
import { mockFetch } from '@/test-utils'

beforeEach(() => {
  mockFetch({ data: 'mock response' })
})
```

### Mock Next.js Router

```typescript
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/current-path',
    push: jest.fn(),
    query: {},
  }),
}))
```

## Running Tests

### Development

```bash
# Watch mode - runs tests on file changes
npm test -- --watch

# Run specific test file
npm test -- MyComponent.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="renders correctly"
```

### CI/CD

Tests run automatically on GitHub Actions:
- Unit tests on every push/PR
- E2E tests on every push/PR
- Coverage reports uploaded to Codecov

### Coverage

```bash
# Generate coverage report
npm test -- --coverage

# View HTML report
open coverage/lcov-report/index.html  # macOS
xdg-open coverage/lcov-report/index.html  # Linux
```

## Best Practices

### 1. Test User Behavior, Not Implementation

**Good:**
```typescript
it('submits form when button clicked', () => {
  render(<LoginForm />)
  fireEvent.click(screen.getByRole('button', { name: /submit/i }))
  expect(mockSubmit).toHaveBeenCalled()
})
```

**Bad:**
```typescript
it('calls handleSubmit when button clicked', () => {
  // Testing implementation detail
})
```

### 2. Use Testing Library Queries

Prefer (in order):
1. `getByRole` - Most accessible
2. `getByLabelText` - Form inputs
3. `getByText` - Visible text
4. `getByTestId` - Last resort

### 3. Async Testing

```typescript
// Use waitFor for async operations
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// Use findBy for async queries (includes waitFor)
expect(await screen.findByText('Loaded')).toBeInTheDocument()
```

### 4. Mock External Dependencies

- Mock API calls to avoid network requests
- Mock authentication to avoid Clerk SDK
- Mock charts to avoid canvas rendering issues

### 5. Clean Up

```typescript
afterEach(() => {
  jest.clearAllMocks()
})
```

## Troubleshooting

### Tests Timing Out

```typescript
// Increase timeout
await waitFor(
  () => {
    expect(screen.getByText('Loaded')).toBeInTheDocument()
  },
  { timeout: 10000 }
)
```

### "Not wrapped in act(...)" Warning

Use `waitFor` or `findBy` queries:

```typescript
// Instead of this:
fireEvent.click(button)
expect(screen.getByText('Updated')).toBeInTheDocument()

// Do this:
fireEvent.click(button)
await waitFor(() => {
  expect(screen.getByText('Updated')).toBeInTheDocument()
})
```

### Mock Not Working

Ensure mock is defined before component import:

```typescript
// Mock first
jest.mock('next/router', () => ({ ... }))

// Then import
import MyComponent from '@/components/MyComponent'
```

### Playwright Tests Failing Locally

1. Install browsers: `npx playwright install`
2. Start dev server: `npm run dev`
3. Run tests: `npx playwright test`

## E2E Testing Tips

### 1. Use Page Object Pattern

```typescript
// e2e/pages/DashboardPage.ts
export class DashboardPage {
  constructor(private page: Page) {}

  async navigate() {
    await this.page.goto('/dashboard')
  }

  async requestAnalysis() {
    await this.page.click('button:has-text("Request Analysis")')
  }
}
```

### 2. Handle Loading States

```typescript
await page.waitForLoadState('networkidle')
await page.waitForSelector('[data-testid="content"]')
```

### 3. Test Mobile Viewports

```typescript
test('mobile view', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 })
  // ... test mobile behavior
})
```

## Additional Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Next.js Applications](https://nextjs.org/docs/testing)
