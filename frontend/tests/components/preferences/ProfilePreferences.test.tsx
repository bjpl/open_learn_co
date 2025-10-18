/**
 * ProfilePreferences Component Tests
 * Tests for profile preferences component
 */

import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProfilePreferences } from '@/components/preferences/ProfilePreferences'
import { renderWithProviders } from '../../utils/test-utils'
import { mockProfilePreferences } from '../../fixtures/preferences'

// Mock the preferences hook
jest.mock('@/lib/preferences/use-preferences', () => ({
  usePreferences: () => ({
    preferences: {
      profile: mockProfilePreferences,
    },
    updateProfile: jest.fn(),
    loading: false,
  }),
}))

describe('ProfilePreferences', () => {
  it('renders all profile fields', () => {
    renderWithProviders(<ProfilePreferences />)

    expect(screen.getByText('Profile Settings')).toBeInTheDocument()
    expect(screen.getByLabelText('Full Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument()
    expect(screen.getByLabelText('Bio')).toBeInTheDocument()
    expect(screen.getByLabelText('Preferred Language')).toBeInTheDocument()
    expect(screen.getByLabelText('Timezone')).toBeInTheDocument()
    expect(screen.getByLabelText('Date Format')).toBeInTheDocument()
  })

  it('displays current profile values', () => {
    renderWithProviders(<ProfilePreferences />)

    const nameInput = screen.getByLabelText('Full Name') as HTMLInputElement
    const emailInput = screen.getByLabelText('Email Address') as HTMLInputElement

    expect(nameInput.value).toBe(mockProfilePreferences.fullName)
    expect(emailInput.value).toBe(mockProfilePreferences.email)
  })

  it('shows avatar upload component', () => {
    renderWithProviders(<ProfilePreferences />)

    expect(screen.getByText('Profile Picture')).toBeInTheDocument()
    expect(screen.getByText('Upload Photo')).toBeInTheDocument()
  })

  it('shows bio character count', () => {
    renderWithProviders(<ProfilePreferences />)

    const bioLength = mockProfilePreferences.bio?.length || 0
    expect(screen.getByText(`${bioLength}/500 characters`)).toBeInTheDocument()
  })

  it('shows email verification notice', () => {
    renderWithProviders(<ProfilePreferences />)

    expect(
      screen.getByText(/You'll need to verify your new email/i)
    ).toBeInTheDocument()
  })

  it('renders language options', () => {
    renderWithProviders(<ProfilePreferences />)

    const languageSelect = screen.getByLabelText('Preferred Language')
    expect(languageSelect).toBeInTheDocument()
  })

  it('renders timezone options', () => {
    renderWithProviders(<ProfilePreferences />)

    const timezoneSelect = screen.getByLabelText('Timezone')
    expect(timezoneSelect).toBeInTheDocument()
  })

  it('renders date format options', () => {
    renderWithProviders(<ProfilePreferences />)

    const dateFormatSelect = screen.getByLabelText('Date Format')
    expect(dateFormatSelect).toBeInTheDocument()
  })

  it('enforces bio max length', () => {
    renderWithProviders(<ProfilePreferences />)

    const bioTextarea = screen.getByLabelText('Bio') as HTMLTextAreaElement
    expect(bioTextarea).toHaveAttribute('maxLength', '500')
  })
})
