/**
 * User Preferences Page
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Settings, User, Bell, Monitor, GraduationCap, Shield, Database, Save, RotateCcw, AlertCircle, CheckCircle } from 'lucide-react'
import { PreferencesProvider, usePreferencesContext } from '@/lib/preferences/preferences-context'
import { ProfilePreferences } from '@/components/preferences/ProfilePreferences'
import { NotificationPreferences } from '@/components/preferences/NotificationPreferences'
import { DisplayPreferences } from '@/components/preferences/DisplayPreferences'
import { LanguagePreferences } from '@/components/preferences/LanguagePreferences'
import { PrivacyPreferences } from '@/components/preferences/PrivacyPreferences'
import { DataManagement } from '@/components/preferences/DataManagement'
import { RouteErrorBoundary } from '@/components/error-boundary'
import { useUserId, useIsAuthenticated } from '@/hooks/useAuth'
import { logger } from '@/utils/logger'
// Phase 1: useCurrentUser not needed yet

type Tab = 'profile' | 'notifications' | 'display' | 'learning' | 'privacy' | 'data'

interface TabConfig {
  id: Tab
  label: string
  icon: React.ComponentType<{ className?: string }>
}

const TABS: TabConfig[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'display', label: 'Display', icon: Monitor },
  { id: 'learning', label: 'Language', icon: GraduationCap },
  { id: 'privacy', label: 'Privacy', icon: Shield },
  { id: 'data', label: 'Data', icon: Database },
]

function PreferencesContent() {
  const [activeTab, setActiveTab] = useState<Tab>('profile')
  const [showSaveButton, setShowSaveButton] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')

  const {
    hasUnsavedChanges,
    savePreferences,
    undoLastChange,
    error,
  } = usePreferencesContext()

  // Show sticky save button when scrolling and there are unsaved changes
  useEffect(() => {
    const handleScroll = () => {
      setShowSaveButton(window.scrollY > 100 && hasUnsavedChanges)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [hasUnsavedChanges])

  // Warn before leaving page with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedChanges])

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      await savePreferences()
      setSaveStatus('success')
      setTimeout(() => setSaveStatus('idle'), 3000)
    } catch (error) {
      logger.error('Failed to save preferences', error)
      setSaveStatus('error')
    }
  }

  const handleUndo = () => {
    undoLastChange()
    setSaveStatus('idle')
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return <ProfilePreferences />
      case 'notifications':
        return <NotificationPreferences />
      case 'display':
        return <DisplayPreferences />
      case 'learning':
        return <LanguagePreferences />
      case 'privacy':
        return <PrivacyPreferences />
      case 'data':
        return <DataManagement />
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-yellow-500 to-orange-600 text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center">
            <Settings className="h-8 w-8 mr-3" />
            <div>
              <h1 className="text-3xl font-bold">User Preferences</h1>
              <p className="text-yellow-100 mt-1">
                Customize your OpenLearn Colombia experience
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="container mx-auto px-4 mt-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-3 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-red-900 dark:text-red-200">
                  Error saving preferences
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {error.message}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {hasUnsavedChanges && (
        <div className="container mx-auto px-4 mt-4">
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-3" />
                <p className="text-sm text-yellow-900 dark:text-yellow-200">
                  You have unsaved changes. Changes are auto-saved after 1 second.
                </p>
              </div>
              <button
                onClick={handleUndo}
                className="text-sm font-medium text-yellow-700 dark:text-yellow-300 hover:text-yellow-800 dark:hover:text-yellow-200"
              >
                Undo
              </button>
            </div>
          </div>
        </div>
      )}

      {saveStatus === 'success' && (
        <div className="container mx-auto px-4 mt-4">
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mr-3" />
              <p className="text-sm text-green-900 dark:text-green-200">
                Preferences saved successfully!
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Tabs */}
          <nav className="lg:w-64 flex-shrink-0">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-2 space-y-1">
              {TABS.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      w-full flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors
                      ${
                        activeTab === tab.id
                          ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-900 dark:text-yellow-200'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                  >
                    <Icon className="h-5 w-5 mr-3" />
                    {tab.label}
                  </button>
                )
              })}
            </div>

            {/* Action Buttons (Desktop) */}
            <div className="hidden lg:block mt-6 space-y-3">
              <button
                onClick={handleSave}
                disabled={!hasUnsavedChanges || saveStatus === 'saving'}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="h-4 w-4 mr-2" />
                {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
              </button>

              <button
                onClick={handleUndo}
                disabled={!hasUnsavedChanges}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Undo Changes
              </button>
            </div>
          </nav>

          {/* Tab Content */}
          <div className="flex-1">
            {renderTabContent()}
          </div>
        </div>
      </div>

      {/* Sticky Save Button (Mobile & when scrolling) */}
      {showSaveButton && (
        <div className="fixed bottom-4 right-4 z-50">
          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving'}
            className="inline-flex items-center px-6 py-3 border border-transparent rounded-full shadow-lg text-base font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
          >
            <Save className="h-5 w-5 mr-2" />
            {saveStatus === 'saving' ? 'Saving...' : 'Save'}
          </button>
        </div>
      )}

      {/* Mobile Action Buttons */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 space-y-2">
        <button
          onClick={handleSave}
          disabled={!hasUnsavedChanges || saveStatus === 'saving'}
          className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
        >
          <Save className="h-4 w-4 mr-2" />
          {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}

export default function PreferencesPage() {
  const userId = useUserId()
  const isAuthenticated = useIsAuthenticated()
  // const currentUser = useCurrentUser() // Phase 1: Not used yet

  // Redirect to login if not authenticated
  if (!isAuthenticated || !userId) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Authentication Required
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Please log in to access your preferences.
          </p>
          <a
            href="/login"
            className="inline-flex items-center px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-yellow-600 hover:bg-yellow-700"
          >
            Go to Login
          </a>
        </div>
      </div>
    )
  }

  return (
    <RouteErrorBoundary>
      <PreferencesProvider userId={userId} enableAutoSave={true} autoSaveDelay={1000}>
        <PreferencesContent />
      </PreferencesProvider>
    </RouteErrorBoundary>
  )
}
