import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('navigates between main pages', async ({ page }) => {
    // Start at home
    await page.goto('/')

    // Navigate to dashboard
    await page.click('a:has-text("Dashboard")')
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator('h1')).toContainText(/dashboard/i)

    // Navigate to analysis
    await page.click('a:has-text("Analysis")')
    await expect(page).toHaveURL(/\/analysis/)

    // Navigate to accounts
    await page.click('a:has-text("Accounts")')
    await expect(page).toHaveURL(/\/accounts/)

    // Navigate back to dashboard
    await page.click('a:has-text("Dashboard")')
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('shows active link highlighting', async ({ page }) => {
    await page.goto('/dashboard')

    // Dashboard link should be active
    const dashboardLink = page.locator('nav a:has-text("Dashboard")')
    await expect(dashboardLink).toHaveClass(/active|current/)

    // Navigate to analysis
    await page.click('a:has-text("Analysis")')

    // Analysis link should now be active
    const analysisLink = page.locator('nav a:has-text("Analysis")')
    await expect(analysisLink).toHaveClass(/active|current/)
  })

  test('user menu is accessible', async ({ page }) => {
    await page.goto('/dashboard')

    // User button should be visible
    const userButton = page.locator('[data-testid="user-button"]')
    await expect(userButton).toBeVisible()

    // Click to open menu (if implemented)
    await userButton.click()

    // Should show user options (adjust selectors based on implementation)
    // await expect(page.locator('text=/sign out|account|profile/i')).toBeVisible()
  })
})
