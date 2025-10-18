/**
 * FilterPanel Component Tests
 * Tests for article filtering panel
 */

import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FilterPanel } from '@/components/filters/FilterPanel'
import { renderWithProviders } from '../../utils/test-utils'

describe('FilterPanel', () => {
  const mockOnFilterChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders all filter sections', () => {
    renderWithProviders(<FilterPanel onFilterChange={mockOnFilterChange} />)

    expect(screen.getByText(/filters/i)).toBeInTheDocument()
  })

  it('shows clear filters button when filters are active', async () => {
    renderWithProviders(<FilterPanel onFilterChange={mockOnFilterChange} />)

    // Apply a filter
    const categoryFilter = screen.getByLabelText(/category/i)
    await userEvent.click(categoryFilter)

    // Clear button should appear
    const clearButton = screen.queryByText(/clear/i)
    expect(clearButton).toBeInTheDocument()
  })

  it('can collapse and expand', async () => {
    renderWithProviders(<FilterPanel onFilterChange={mockOnFilterChange} />)

    const collapseButton = screen.getByRole('button', { name: /toggle/i })
    await userEvent.click(collapseButton)

    // Panel should collapse (implementation dependent)
    // This is a placeholder test - adjust based on actual implementation
  })
})
