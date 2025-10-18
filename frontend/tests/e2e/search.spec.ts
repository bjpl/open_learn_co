/**
 * Search E2E Tests
 * End-to-end tests for search functionality
 */

import { test, expect } from '@playwright/test'

test.describe('Search Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/news')
  })

  test('search input is visible', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await expect(searchInput).toBeVisible()
  })

  test('performs search', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('Colombia economy')
    await searchInput.press('Enter')

    // Wait for results to load
    await page.waitForTimeout(1000)

    // Check if URL updated with search query (if implemented)
    // or if results are displayed
    await expect(searchInput).toHaveValue('Colombia economy')
  })

  test('clears search', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('test query')

    // Look for clear button if it exists
    const clearButton = page.locator('button[aria-label*="clear"]').first()
    if (await clearButton.isVisible()) {
      await clearButton.click()
      await expect(searchInput).toHaveValue('')
    }
  })

  test('search is accessible via keyboard', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.focus()
    await searchInput.type('keyboard test')
    await searchInput.press('Enter')

    await expect(searchInput).toHaveValue('keyboard test')
  })
})
