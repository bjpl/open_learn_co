/**
 * FilterTag Component Tests
 * Tests for filter tag component
 */

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FilterTag } from '@/components/ui/FilterTag'

describe('FilterTag', () => {
  const mockOnRemove = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders tag label', () => {
    render(<FilterTag label="Politics" onRemove={mockOnRemove} />)

    expect(screen.getByText('Politics')).toBeInTheDocument()
  })

  it('calls onRemove when clicked', async () => {
    render(<FilterTag label="Politics" onRemove={mockOnRemove} />)

    const removeButton = screen.getByRole('button')
    await userEvent.click(removeButton)

    expect(mockOnRemove).toHaveBeenCalledTimes(1)
  })

  it('applies variant styles', () => {
    const { container } = render(
      <FilterTag label="Test" onRemove={mockOnRemove} variant="primary" />
    )

    // Should have variant-specific classes
    expect(container.firstChild).toHaveClass('bg-yellow-100')
  })

  it('can be disabled', () => {
    render(<FilterTag label="Test" onRemove={mockOnRemove} disabled />)

    const removeButton = screen.getByRole('button')
    expect(removeButton).toBeDisabled()
  })

  it('shows remove icon', () => {
    const { container } = render(
      <FilterTag label="Test" onRemove={mockOnRemove} />
    )

    // X icon should be present
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })
})
