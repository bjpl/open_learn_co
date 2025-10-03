/**
 * Select Dropdown Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'

export interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  id?: string
  name?: string
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  label?: string
  placeholder?: string
  disabled?: boolean
  error?: string
  className?: string
}

export function Select({
  id,
  name,
  value,
  onChange,
  options,
  label,
  placeholder,
  disabled = false,
  error,
  className = '',
}: SelectProps) {
  return (
    <div className={className}>
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
        >
          {label}
        </label>
      )}
      <select
        id={id}
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`
          block w-full rounded-md border-gray-300 dark:border-gray-600
          bg-white dark:bg-gray-700 text-gray-900 dark:text-white
          shadow-sm focus:border-yellow-500 focus:ring-yellow-500
          sm:text-sm
          ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  )
}
