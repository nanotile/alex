import { test as setup, expect } from '@playwright/test'

const authFile = 'playwright/.auth/user.json'

/**
 * Authentication setup for Playwright tests
 *
 * This runs once before tests and saves authentication state.
 * Individual tests can then reuse this auth state.
 */
setup('authenticate', async ({ page }) => {
  // Navigate to sign-in page
  await page.goto('/sign-in')

  // Fill in login credentials
  // NOTE: In real tests, use environment variables for credentials
  const testEmail = process.env.E2E_TEST_EMAIL || 'test@example.com'
  const testPassword = process.env.E2E_TEST_PASSWORD || 'testpassword123'

  // Wait for Clerk sign-in form to load
  await page.waitForSelector('input[name="identifier"]', { timeout: 10000 })

  // Fill credentials
  await page.fill('input[name="identifier"]', testEmail)
  await page.fill('input[name="password"]', testPassword)

  // Submit form
  await page.click('button[type="submit"]')

  // Wait for redirect to dashboard or home
  await page.waitForURL(/\/(dashboard|$)/, { timeout: 15000 })

  // Verify authentication succeeded
  await expect(page.locator('[data-testid="user-button"]')).toBeVisible()

  // Save authentication state
  await page.context().storageState({ path: authFile })
})
