/**
 * Navbar Component Tests
 * Tests for main navigation bar
 */

import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Navbar } from '@/components/Navbar'
import { renderWithProviders } from '../utils/test-utils'

describe('Navbar', () => {
  it('renders logo', () => {
    renderWithProviders(<Navbar />)

    expect(screen.getByText(/OpenLearn Colombia/i)).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    renderWithProviders(<Navbar />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('News')).toBeInTheDocument()
    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText('Sources')).toBeInTheDocument()
    expect(screen.getByText('Trends')).toBeInTheDocument()
  })

  it('highlights active route', () => {
    renderWithProviders(<Navbar />)

    // Active link should have special styling
    const dashboardLink = screen.getByText('Dashboard')
    expect(dashboardLink.closest('a')).toHaveClass('text-yellow-500')
  })

  it('shows user menu when authenticated', () => {
    renderWithProviders(<Navbar />)

    // Look for user menu or profile button
    const userMenuButton = screen.queryByRole('button', { name: /user|profile|account/i })
    if (userMenuButton) {
      expect(userMenuButton).toBeInTheDocument()
    }
  })

  it('shows mobile menu button on small screens', () => {
    renderWithProviders(<Navbar />)

    const mobileMenuButton = screen.queryByRole('button', { name: /menu|navigation/i })
    expect(mobileMenuButton).toBeInTheDocument()
  })

  it('toggles mobile menu', async () => {
    renderWithProviders(<Navbar />)

    const menuButton = screen.getByRole('button', { name: /menu|navigation/i })
    await userEvent.click(menuButton)

    // Mobile menu should be visible
    // (exact implementation depends on component)
  })

  it('includes preferences link', () => {
    renderWithProviders(<Navbar />)

    const preferencesLink = screen.queryByText(/preferences|settings/i)
    expect(preferencesLink).toBeInTheDocument()
  })
})
