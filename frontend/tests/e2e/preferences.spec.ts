/**
 * Preferences E2E Tests
 * End-to-end tests for user preferences
 */

import { test, expect } from '@playwright/test'

test.describe('User Preferences', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/preferences')
  })

  test('loads preferences page', async ({ page }) => {
    await expect(page.getByText('User Preferences')).toBeVisible()
  })

  test('displays all preference sections', async ({ page }) => {
    await expect(page.getByText('Profile Settings')).toBeVisible()
    await expect(page.getByText('Notification Settings')).toBeVisible()
    await expect(page.getByText('Display Settings')).toBeVisible()
    await expect(page.getByText('Privacy Settings')).toBeVisible()
  })

  test('updates profile name', async ({ page }) => {
    const nameInput = page.getByLabel('Full Name')
    await nameInput.clear()
    await nameInput.fill('New Test Name')

    // Value should be updated
    await expect(nameInput).toHaveValue('New Test Name')
  })

  test('updates email', async ({ page }) => {
    const emailInput = page.getByLabel('Email Address')
    await emailInput.clear()
    await emailInput.fill('newemail@test.com')

    await expect(emailInput).toHaveValue('newemail@test.com')
  })

  test('changes language preference', async ({ page }) => {
    const languageSelect = page.getByLabel('Preferred Language')
    await languageSelect.selectOption('en')

    await expect(languageSelect).toHaveValue('en')
  })

  test('uploads avatar', async ({ page }) => {
    const uploadButton = page.getByText('Upload Photo')
    await expect(uploadButton).toBeVisible()

    // Note: Actual file upload would require a real file path
    // This tests that the button is clickable
    await expect(uploadButton).toBeEnabled()
  })

  test('toggles notification preferences', async ({ page }) => {
    const emailNotifications = page.getByLabel('Email Notifications')
    const isChecked = await emailNotifications.isChecked()

    await emailNotifications.click()

    // Should toggle state
    await expect(emailNotifications).toHaveAttribute(
      'checked',
      isChecked ? '' : 'checked'
    )
  })

  test('changes theme', async ({ page }) => {
    const themeSelect = page.getByLabel('Theme')
    await themeSelect.selectOption('dark')

    await expect(themeSelect).toHaveValue('dark')
  })

  test('is responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.getByText('Profile Settings')).toBeVisible()
    // Tabs should stack vertically on mobile
  })
})
