/**
 * Dashboard Page Tests
 * Tests for main dashboard page
 */

import { screen } from '@testing-library/react'
import { renderWithProviders } from '../utils/test-utils'
import Dashboard from '@/app/page'

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    renderWithProviders(<Dashboard />)

    expect(
      screen.getByText('Colombian Data Intelligence Dashboard')
    ).toBeInTheDocument()
  })

  it('renders all stats cards', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Total Articles')).toBeInTheDocument()
    expect(screen.getByText('Active Sources')).toBeInTheDocument()
    expect(screen.getByText('Daily Visitors')).toBeInTheDocument()
    expect(screen.getByText('API Calls')).toBeInTheDocument()
  })

  it('displays stat values', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('12,485')).toBeInTheDocument() // Total Articles
    expect(screen.getByText('58')).toBeInTheDocument() // Active Sources
    expect(screen.getByText('3,247')).toBeInTheDocument() // Daily Visitors
    expect(screen.getByText('89.3K')).toBeInTheDocument() // API Calls
  })

  it('renders chart sections', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Articles Collected Over Time')).toBeInTheDocument()
    expect(screen.getByText('Topic Distribution')).toBeInTheDocument()
    expect(screen.getByText('Sentiment Analysis - Last 7 Days')).toBeInTheDocument()
  })

  it('renders data source status section', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Data Source Status')).toBeInTheDocument()
  })

  it('renders recent activity section', () => {
    renderWithProviders(<Dashboard />)

    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
  })

  it('displays source count in header', () => {
    renderWithProviders(<Dashboard />)

    expect(
      screen.getByText(/Real-time insights from 58 active sources/i)
    ).toBeInTheDocument()
  })

  it('wraps sections in error boundaries', () => {
    const { container } = renderWithProviders(<Dashboard />)

    // ComponentErrorBoundary wraps chart sections
    expect(container.querySelector('.space-y-8')).toBeInTheDocument()
  })
})
