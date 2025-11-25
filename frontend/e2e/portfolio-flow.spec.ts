import { test, expect } from '@playwright/test'

test.describe('Portfolio Analysis Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start at dashboard
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
  })

  test('complete analysis workflow', async ({ page }) => {
    // Verify dashboard loaded
    await expect(page.locator('h1')).toContainText(/dashboard/i)

    // Check that portfolio data is visible
    await expect(page.locator('text=/account/i').first()).toBeVisible()

    // Click request analysis button
    await page.click('button:has-text("Request Analysis")')

    // Should navigate to analysis page or show modal
    await page.waitForURL(/\/analysis/, { timeout: 5000 })

    // Wait for job to be created
    await expect(page.locator('text=/pending|in progress/i')).toBeVisible({
      timeout: 10000,
    })

    // Wait for analysis to complete (with longer timeout)
    await expect(page.locator('text=/completed/i')).toBeVisible({
      timeout: 180000, // 3 minutes max
    })

    // Verify results are displayed
    await expect(page.locator('.portfolio-report, [data-testid="report"]')).toBeVisible()

    // Verify charts are rendered
    const charts = page.locator('[data-testid*="chart"], canvas, svg')
    await expect(charts.first()).toBeVisible()

    // Verify retirement projection is shown
    await expect(page.locator('text=/retirement|projection/i')).toBeVisible()
  })

  test('view portfolio accounts', async ({ page }) => {
    // Click on first account
    const firstAccount = page.locator('text=/account/i').first()
    await firstAccount.click()

    // Should navigate to account detail page
    await page.waitForURL(/\/accounts\//, { timeout: 5000 })

    // Verify account details are shown
    await expect(page.locator('text=/position|holding/i')).toBeVisible()
    await expect(page.locator('text=/cash balance/i')).toBeVisible()
  })

  test('handles errors gracefully', async ({ page }) => {
    // Intercept API call and return error
    await page.route('**/api/analyze', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      })
    })

    // Try to request analysis
    await page.click('button:has-text("Request Analysis")')

    // Should show error message
    await expect(page.locator('text=/error|failed/i')).toBeVisible({
      timeout: 5000,
    })
  })
})
