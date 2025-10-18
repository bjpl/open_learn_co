/**
 * AvatarUpload Component Tests
 * Tests for avatar upload functionality
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AvatarUpload } from '@/components/ui/AvatarUpload'
import { createMockFile } from '../../utils/test-utils'

describe('AvatarUpload', () => {
  const mockOnUpload = jest.fn()
  const mockOnRemove = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without avatar', () => {
    render(<AvatarUpload onUpload={mockOnUpload} />)

    expect(screen.getByText('Upload Photo')).toBeInTheDocument()
    expect(screen.getByText(/PNG, JPG, GIF up to 5MB/i)).toBeInTheDocument()
  })

  it('renders with existing avatar', () => {
    render(
      <AvatarUpload
        currentAvatar="data:image/png;base64,mockdata"
        onUpload={mockOnUpload}
        onRemove={mockOnRemove}
      />
    )

    const avatar = screen.getByAltText('Avatar')
    expect(avatar).toBeInTheDocument()
    expect(avatar).toHaveAttribute('src', 'data:image/png;base64,mockdata')
  })

  it('handles file upload', async () => {
    render(<AvatarUpload onUpload={mockOnUpload} />)

    const file = createMockFile('test.png', 1024, 'image/png')
    const input = screen.getByLabelText(/upload photo/i) as HTMLInputElement

    await userEvent.upload(input, file)

    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith(file)
    })
  })

  it('validates file size', async () => {
    render(
      <AvatarUpload
        onUpload={mockOnUpload}
        maxSize={1024} // 1KB max
      />
    )

    const largeFile = createMockFile('large.png', 2048, 'image/png') // 2KB
    const input = screen.getByLabelText(/upload photo/i) as HTMLInputElement

    await userEvent.upload(input, largeFile)

    await waitFor(() => {
      expect(screen.getByText(/File size must be less than/i)).toBeInTheDocument()
      expect(mockOnUpload).not.toHaveBeenCalled()
    })
  })

  it('validates file type', async () => {
    render(<AvatarUpload onUpload={mockOnUpload} />)

    const textFile = createMockFile('test.txt', 1024, 'text/plain')
    const input = screen.getByLabelText(/upload photo/i) as HTMLInputElement

    await userEvent.upload(input, textFile)

    await waitFor(() => {
      expect(screen.getByText('File must be an image')).toBeInTheDocument()
      expect(mockOnUpload).not.toHaveBeenCalled()
    })
  })

  it('handles avatar removal', async () => {
    render(
      <AvatarUpload
        currentAvatar="data:image/png;base64,mockdata"
        onUpload={mockOnUpload}
        onRemove={mockOnRemove}
      />
    )

    const removeButton = screen.getByRole('button', { name: '' }) // X button
    await userEvent.click(removeButton)

    expect(mockOnRemove).toHaveBeenCalled()
  })

  it('disables upload when disabled prop is true', () => {
    render(<AvatarUpload onUpload={mockOnUpload} disabled />)

    const uploadButton = screen.getByText('Upload Photo')
    expect(uploadButton).toBeDisabled()
  })

  it('shows correct max size in help text', () => {
    render(
      <AvatarUpload
        onUpload={mockOnUpload}
        maxSize={10 * 1024 * 1024} // 10MB
      />
    )

    expect(screen.getByText(/PNG, JPG, GIF up to 10MB/i)).toBeInTheDocument()
  })
})
