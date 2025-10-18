/**
 * Dashboard E2E Tests
 * End-to-end tests for dashboard functionality
 */

import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('loads successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/OpenLearn Colombia|Colombian Data Intelligence/)
    await expect(
      page.getByText('Colombian Data Intelligence Dashboard')
    ).toBeVisible()
  })

  test('displays all stat cards', async ({ page }) => {
    await expect(page.getByText('Total Articles')).toBeVisible()
    await expect(page.getByText('Active Sources')).toBeVisible()
    await expect(page.getByText('Daily Visitors')).toBeVisible()
    await expect(page.getByText('API Calls')).toBeVisible()
  })

  test('shows stat values', async ({ page }) => {
    await expect(page.getByText('12,485')).toBeVisible()
    await expect(page.getByText('58')).toBeVisible()
    await expect(page.getByText('3,247')).toBeVisible()
    await expect(page.getByText('89.3K')).toBeVisible()
  })

  test('renders charts', async ({ page }) => {
    await expect(page.getByText('Articles Collected Over Time')).toBeVisible()
    await expect(page.getByText('Topic Distribution')).toBeVisible()
    await expect(page.getByText('Sentiment Analysis - Last 7 Days')).toBeVisible()
  })

  test('displays data source status', async ({ page }) => {
    await expect(page.getByText('Data Source Status')).toBeVisible()
  })

  test('shows recent activity feed', async ({ page }) => {
    await expect(page.getByText('Recent Activity')).toBeVisible()
  })

  test('is responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(
      page.getByText('Colombian Data Intelligence Dashboard')
    ).toBeVisible()

    // Stats should still be visible in mobile view
    await expect(page.getByText('Total Articles')).toBeVisible()
  })
})
