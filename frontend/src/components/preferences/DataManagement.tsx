/**
 * Data Management Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React, { useState } from 'react'
import { Download, Trash2, AlertTriangle } from 'lucide-react'
import { usePreferences } from '@/lib/preferences/use-preferences'
import { PreferenceCard } from '@/components/ui/PreferenceCard'
import { exportUserData, deleteUserAccount } from '@/lib/preferences/preferences-api'

export function DataManagement() {
  const { preferences, resetPreferences } = usePreferences()
  const [isExporting, setIsExporting] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  if (!preferences) return null

  const handleExportData = async (format: 'json' | 'csv') => {
    setIsExporting(true)
    try {
      const blob = await exportUserData(preferences.userId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `openlearn-data-${Date.now()}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export data:', error)
      alert('Failed to export data. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const handleClearProgress = async () => {
    if (!confirm('Are you sure you want to clear your vocabulary progress? This cannot be undone.')) {
      return
    }

    // TODO: Implement clear progress API call
    alert('Clear progress functionality will be implemented in the backend.')
  }

  const handleResetPreferences = async () => {
    if (!confirm('Are you sure you want to reset all preferences to defaults?')) {
      return
    }

    try {
      await resetPreferences()
      alert('Preferences reset to defaults successfully.')
    } catch (error) {
      console.error('Failed to reset preferences:', error)
      alert('Failed to reset preferences. Please try again.')
    }
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') {
      alert('Please type DELETE to confirm account deletion.')
      return
    }

    setIsDeleting(true)
    try {
      await deleteUserAccount(preferences.userId)
      alert('Your account has been deleted. You will be logged out.')
      // TODO: Trigger logout and redirect
      window.location.href = '/'
    } catch (error) {
      console.error('Failed to delete account:', error)
      alert('Failed to delete account. Please try again or contact support.')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Export Data */}
      <PreferenceCard
        title="Export Your Data"
        description="Download a copy of your data (GDPR compliance)"
        icon={Download}
      >
        <div className="flex gap-3">
          <button
            onClick={() => handleExportData('json')}
            disabled={isExporting}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
          >
            <Download className="h-4 w-4 mr-2" />
            {isExporting ? 'Exporting...' : 'Export as JSON'}
          </button>

          <button
            onClick={() => handleExportData('csv')}
            disabled={isExporting}
            className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
          >
            <Download className="h-4 w-4 mr-2" />
            {isExporting ? 'Exporting...' : 'Export as CSV'}
          </button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Includes your profile, preferences, vocabulary progress, and learning history
        </p>
      </PreferenceCard>

      {/* Clear Data */}
      <PreferenceCard
        title="Clear Learning Data"
        description="Remove specific data from your account"
        icon={Trash2}
      >
        <div className="space-y-3">
          <button
            onClick={handleClearProgress}
            className="inline-flex items-center px-4 py-2 border border-orange-300 dark:border-orange-600 rounded-md shadow-sm text-sm font-medium text-orange-700 dark:text-orange-300 bg-white dark:bg-gray-700 hover:bg-orange-50 dark:hover:bg-orange-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear Vocabulary Progress
          </button>

          <button
            onClick={handleResetPreferences}
            className="inline-flex items-center px-4 py-2 border border-orange-300 dark:border-orange-600 rounded-md shadow-sm text-sm font-medium text-orange-700 dark:text-orange-300 bg-white dark:bg-gray-700 hover:bg-orange-50 dark:hover:bg-orange-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
          >
            Reset All Preferences
          </button>
        </div>
      </PreferenceCard>

      {/* Delete Account */}
      <PreferenceCard
        title="Delete Account"
        description="Permanently delete your account and all associated data"
        icon={AlertTriangle}
      >
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 mr-3 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-red-900 dark:text-red-200">
                Warning: This action cannot be undone
              </h4>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                Deleting your account will permanently remove all your data, including:
              </p>
              <ul className="mt-2 text-sm text-red-700 dark:text-red-300 list-disc list-inside space-y-1">
                <li>Profile information and preferences</li>
                <li>Vocabulary progress and learning history</li>
                <li>Saved articles and bookmarks</li>
                <li>All personal data</li>
              </ul>
            </div>
          </div>
        </div>

        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="inline-flex items-center px-4 py-2 border border-red-300 dark:border-red-600 rounded-md shadow-sm text-sm font-medium text-red-700 dark:text-red-300 bg-white dark:bg-gray-700 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete My Account
          </button>
        ) : (
          <div className="space-y-3">
            <div>
              <label
                htmlFor="deleteConfirm"
                className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
              >
                Type <strong>DELETE</strong> to confirm:
              </label>
              <input
                type="text"
                id="deleteConfirm"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                placeholder="Type DELETE"
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirmText !== 'DELETE' || isDeleting}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                {isDeleting ? 'Deleting...' : 'Confirm Delete Account'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setDeleteConfirmText('')
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </PreferenceCard>
    </div>
  )
}
