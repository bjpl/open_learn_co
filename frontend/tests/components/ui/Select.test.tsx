/**
 * Select Component Tests
 * Tests for custom select dropdown component
 */

import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Select } from '@/components/ui/Select'

describe('Select', () => {
  const mockOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
  ]

  const mockOnChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders with label', () => {
    render(
      <Select
        id="test-select"
        label="Test Label"
        value="option1"
        onChange={mockOnChange}
        options={mockOptions}
      />
    )

    expect(screen.getByText('Test Label')).toBeInTheDocument()
  })

  it('displays selected value', () => {
    render(
      <Select
        id="test-select"
        value="option2"
        onChange={mockOnChange}
        options={mockOptions}
      />
    )

    const select = screen.getByRole('combobox') as HTMLSelectElement
    expect(select.value).toBe('option2')
  })

  it('renders all options', () => {
    render(
      <Select
        id="test-select"
        value="option1"
        onChange={mockOnChange}
        options={mockOptions}
      />
    )

    mockOptions.forEach((option) => {
      expect(screen.getByText(option.label)).toBeInTheDocument()
    })
  })

  it('calls onChange when value changes', async () => {
    render(
      <Select
        id="test-select"
        value="option1"
        onChange={mockOnChange}
        options={mockOptions}
      />
    )

    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, 'option3')

    expect(mockOnChange).toHaveBeenCalledWith('option3')
  })

  it('can be disabled', () => {
    render(
      <Select
        id="test-select"
        value="option1"
        onChange={mockOnChange}
        options={mockOptions}
        disabled
      />
    )

    const select = screen.getByRole('combobox')
    expect(select).toBeDisabled()
  })

  it('shows placeholder when provided', () => {
    render(
      <Select
        id="test-select"
        value=""
        onChange={mockOnChange}
        options={mockOptions}
        placeholder="Select an option"
      />
    )

    expect(screen.getByText('Select an option')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <Select
        id="test-select"
        value="option1"
        onChange={mockOnChange}
        options={mockOptions}
        className="custom-class"
      />
    )

    const wrapper = container.firstChild
    expect(wrapper).toHaveClass('custom-class')
  })
})
