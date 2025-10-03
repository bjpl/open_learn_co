/**
 * Preference Card Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'
import { LucideIcon } from 'lucide-react'

interface PreferenceCardProps {
  title: string
  description?: string
  icon?: LucideIcon
  children: React.ReactNode
  className?: string
}

export function PreferenceCard({
  title,
  description,
  icon: Icon,
  children,
  className = '',
}: PreferenceCardProps) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 ${className}`}>
      <div className="flex items-start mb-4">
        {Icon && (
          <div className="mr-3 p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
            <Icon className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
          </div>
        )}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          {description && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {description}
            </p>
          )}
        </div>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  )
}
