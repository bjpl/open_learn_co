/**
 * Navigation E2E Tests
 * End-to-end tests for site navigation
 */

import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('navigates to News page', async ({ page }) => {
    await page.click('text=News')
    await expect(page).toHaveURL(/\/news/)
  })

  test('navigates to Analytics page', async ({ page }) => {
    await page.click('text=Analytics')
    await expect(page).toHaveURL(/\/analytics/)
  })

  test('navigates to Sources page', async ({ page }) => {
    await page.click('text=Sources')
    await expect(page).toHaveURL(/\/sources/)
  })

  test('navigates to Trends page', async ({ page }) => {
    await page.click('text=Trends')
    await expect(page).toHaveURL(/\/trends/)
  })

  test('logo click returns to dashboard', async ({ page }) => {
    // Navigate away from home
    await page.click('text=News')
    await expect(page).toHaveURL(/\/news/)

    // Click logo to return
    await page.click('text=OpenLearn Colombia')
    await expect(page).toHaveURL('/')
  })

  test('navigation is accessible via keyboard', async ({ page }) => {
    // Tab to navigation
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Press Enter to activate link
    await page.keyboard.press('Enter')

    // Should navigate somewhere
    await expect(page).not.toHaveURL('/')
  })
})
