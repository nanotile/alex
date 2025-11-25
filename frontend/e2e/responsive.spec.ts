import { test, expect } from '@playwright/test'

test.describe('Responsive Design', () => {
  const viewports = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Desktop', width: 1280, height: 720 },
  ]

  for (const viewport of viewports) {
    test(`renders correctly on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      })

      await page.goto('/dashboard')

      // Main content should be visible
      await expect(page.locator('main')).toBeVisible()

      // Navigation should be accessible (might be in hamburger menu on mobile)
      if (viewport.width < 768) {
        // Mobile: check for hamburger menu
        const mobileMenu = page.locator('[aria-label="menu"], button:has-text("☰")')
        if (await mobileMenu.isVisible()) {
          await mobileMenu.click()
        }
      }

      // Verify key UI elements are accessible
      await expect(
        page.locator('a:has-text("Dashboard"), button:has-text("Dashboard")')
      ).toBeVisible()
    })
  }

  test('charts are responsive', async ({ page }) => {
    await page.goto('/analysis')

    // Wait for a completed analysis to be shown
    await page.waitForSelector('[data-testid="pie-chart"], canvas, svg', {
      timeout: 10000,
    })

    // Test desktop
    await page.setViewportSize({ width: 1280, height: 720 })
    const desktopChart = page.locator('[data-testid="pie-chart"], canvas').first()
    await expect(desktopChart).toBeVisible()

    // Test mobile
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(desktopChart).toBeVisible()
  })
})
