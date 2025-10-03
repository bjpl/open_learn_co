/**
 * Avatar Upload Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React, { useRef, useState } from 'react'
import { Upload, User, X } from 'lucide-react'

interface AvatarUploadProps {
  currentAvatar?: string
  onUpload: (file: File) => void
  onRemove?: () => void
  maxSize?: number // in bytes
  disabled?: boolean
  className?: string
}

export function AvatarUpload({
  currentAvatar,
  onUpload,
  onRemove,
  maxSize = 5 * 1024 * 1024, // 5MB default
  disabled = false,
  className = '',
}: AvatarUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | undefined>(currentAvatar)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file size
    if (file.size > maxSize) {
      setError(`File size must be less than ${Math.round(maxSize / 1024 / 1024)}MB`)
      return
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('File must be an image')
      return
    }

    setError(null)

    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setPreview(reader.result as string)
    }
    reader.readAsDataURL(file)

    // Call upload handler
    onUpload(file)
  }

  const handleRemove = () => {
    setPreview(undefined)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    onRemove?.()
  }

  return (
    <div className={className}>
      <div className="flex items-center space-x-4">
        {/* Avatar Preview */}
        <div className="relative">
          {preview ? (
            <img
              src={preview}
              alt="Avatar"
              className="h-24 w-24 rounded-full object-cover ring-2 ring-gray-200 dark:ring-gray-700"
            />
          ) : (
            <div className="h-24 w-24 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
              <User className="h-12 w-12 text-gray-400 dark:text-gray-500" />
            </div>
          )}
          {preview && onRemove && (
            <button
              type="button"
              onClick={handleRemove}
              disabled={disabled}
              className="absolute -top-1 -right-1 bg-red-500 rounded-full p-1 text-white hover:bg-red-600 transition-colors"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Upload Button */}
        <div className="flex-1">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            disabled={disabled}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className={`
              inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600
              rounded-md shadow-sm text-sm font-medium
              text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700
              hover:bg-gray-50 dark:hover:bg-gray-600
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Photo
          </button>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            PNG, JPG, GIF up to {Math.round(maxSize / 1024 / 1024)}MB
          </p>
          {error && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>
      </div>
    </div>
  )
}
