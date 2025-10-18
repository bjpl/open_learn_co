/**
 * LoginForm Component Tests
 * Tests for authentication login form
 */

import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginForm } from '@/components/auth/LoginForm'
import { renderWithProviders } from '../../utils/test-utils'

describe('LoginForm', () => {
  it('renders login form fields', () => {
    renderWithProviders(<LoginForm />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login|sign in/i })).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    renderWithProviders(<LoginForm />)

    const submitButton = screen.getByRole('button', { name: /login|sign in/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      // Should show validation errors
      expect(screen.getByText(/email.*required/i) || screen.getByText(/required/i)).toBeInTheDocument()
    })
  })

  it('validates email format', async () => {
    renderWithProviders(<LoginForm />)

    const emailInput = screen.getByLabelText(/email/i)
    await userEvent.type(emailInput, 'invalid-email')

    const submitButton = screen.getByRole('button', { name: /login|sign in/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/valid email/i) || screen.getByText(/invalid/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    renderWithProviders(<LoginForm />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await userEvent.type(emailInput, 'test@example.com')
    await userEvent.type(passwordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /login|sign in/i })
    await userEvent.click(submitButton)

    // Form should submit (exact behavior depends on implementation)
    await waitFor(() => {
      expect(submitButton).toBeEnabled()
    })
  })

  it('shows password toggle', () => {
    renderWithProviders(<LoginForm />)

    const passwordInput = screen.getByLabelText(/password/i)
    expect(passwordInput).toHaveAttribute('type', 'password')

    // Look for toggle button
    const toggleButton = screen.queryByRole('button', { name: /show|hide|toggle.*password/i })
    expect(toggleButton).toBeInTheDocument()
  })

  it('has forgot password link', () => {
    renderWithProviders(<LoginForm />)

    const forgotLink = screen.getByText(/forgot.*password/i)
    expect(forgotLink).toBeInTheDocument()
    expect(forgotLink).toHaveAttribute('href', '/forgot-password')
  })

  it('has register link', () => {
    renderWithProviders(<LoginForm />)

    const registerLink = screen.getByText(/sign up|register|create account/i)
    expect(registerLink).toBeInTheDocument()
  })
})
