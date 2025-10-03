/**
 * Radio Group Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'

export interface RadioOption {
  value: string
  label: string
  description?: string
}

interface RadioGroupProps {
  name: string
  options: RadioOption[]
  value: string
  onChange: (value: string) => void
  label?: string
  orientation?: 'vertical' | 'horizontal'
  disabled?: boolean
  className?: string
}

export function RadioGroup({
  name,
  options,
  value,
  onChange,
  label,
  orientation = 'vertical',
  disabled = false,
  className = '',
}: RadioGroupProps) {
  return (
    <fieldset className={className}>
      {label && (
        <legend className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          {label}
        </legend>
      )}
      <div className={`space-${orientation === 'vertical' ? 'y' : 'x'}-3 ${orientation === 'horizontal' ? 'flex flex-wrap gap-3' : ''}`}>
        {options.map((option) => (
          <div key={option.value} className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id={`${name}-${option.value}`}
                name={name}
                type="radio"
                checked={value === option.value}
                onChange={() => onChange(option.value)}
                disabled={disabled}
                className="h-4 w-4 text-yellow-600 border-gray-300 focus:ring-yellow-500 dark:border-gray-600 dark:bg-gray-700"
              />
            </div>
            <div className="ml-3 text-sm">
              <label
                htmlFor={`${name}-${option.value}`}
                className="font-medium text-gray-900 dark:text-white cursor-pointer"
              >
                {option.label}
              </label>
              {option.description && (
                <p className="text-gray-500 dark:text-gray-400">{option.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </fieldset>
  )
}
