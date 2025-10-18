/**
 * StatsCard Component Tests
 * Tests for dashboard statistics card component
 */

import { render, screen } from '@testing-library/react'
import { Activity } from 'lucide-react'
import StatsCard from '@/components/StatsCard'

describe('StatsCard', () => {
  it('renders with all props correctly', () => {
    render(
      <StatsCard
        title="Total Articles"
        value="12,485"
        change={12.5}
        icon={Activity}
        trend="up"
      />
    )

    expect(screen.getByText('Total Articles')).toBeInTheDocument()
    expect(screen.getByText('12,485')).toBeInTheDocument()
    expect(screen.getByText('12.5%')).toBeInTheDocument()
  })

  it('displays positive trend correctly', () => {
    const { container } = render(
      <StatsCard
        title="Test"
        value="100"
        change={5.5}
        icon={Activity}
        trend="up"
      />
    )

    const changeText = screen.getByText('5.5%')
    expect(changeText).toBeInTheDocument()
    // Green color for positive trend
    expect(changeText.parentElement).toHaveClass('text-green-600')
  })

  it('displays negative trend correctly', () => {
    const { container } = render(
      <StatsCard
        title="Test"
        value="100"
        change={-2.3}
        icon={Activity}
        trend="down"
      />
    )

    const changeText = screen.getByText('-2.3%')
    expect(changeText).toBeInTheDocument()
    // Red color for negative trend
    expect(changeText.parentElement).toHaveClass('text-red-600')
  })

  it('renders icon component', () => {
    const { container } = render(
      <StatsCard
        title="Test"
        value="100"
        change={5}
        icon={Activity}
        trend="up"
      />
    )

    // Icon should be rendered (lucide-react icons render as svg)
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('applies correct styling classes', () => {
    const { container } = render(
      <StatsCard
        title="Test"
        value="100"
        change={5}
        icon={Activity}
        trend="up"
      />
    )

    const card = container.firstChild
    expect(card).toHaveClass('bg-white')
    expect(card).toHaveClass('p-6')
    expect(card).toHaveClass('rounded-lg')
  })
})
