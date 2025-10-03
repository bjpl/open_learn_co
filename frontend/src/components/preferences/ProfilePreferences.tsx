/**
 * Profile Preferences Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'
import { User } from 'lucide-react'
import { usePreferences } from '@/lib/preferences/use-preferences'
import { PreferenceCard } from '@/components/ui/PreferenceCard'
import { AvatarUpload } from '@/components/ui/AvatarUpload'
import { Select, SelectOption } from '@/components/ui/Select'
import type { LanguageInterface, DateFormat } from '@/lib/preferences/preferences-types'

const LANGUAGE_OPTIONS: SelectOption[] = [
  { value: 'es', label: 'Español' },
  { value: 'en', label: 'English' },
]

const TIMEZONE_OPTIONS: SelectOption[] = [
  { value: 'America/Bogota', label: 'Bogotá (GMT-5)' },
  { value: 'America/New_York', label: 'New York (GMT-5)' },
  { value: 'America/Los_Angeles', label: 'Los Angeles (GMT-8)' },
  { value: 'Europe/London', label: 'London (GMT+0)' },
  { value: 'Europe/Madrid', label: 'Madrid (GMT+1)' },
]

const DATE_FORMAT_OPTIONS: SelectOption[] = [
  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (31/12/2023)' },
  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (12/31/2023)' },
]

export function ProfilePreferences() {
  const { preferences, updateProfile } = usePreferences()

  if (!preferences) return null

  const { profile } = preferences

  const handleAvatarUpload = async (file: File) => {
    // TODO: Implement actual upload to backend
    const reader = new FileReader()
    reader.onloadend = () => {
      updateProfile({ avatar: reader.result as string })
    }
    reader.readAsDataURL(file)
  }

  const handleAvatarRemove = () => {
    updateProfile({ avatar: undefined })
  }

  return (
    <PreferenceCard
      title="Profile Settings"
      description="Manage your personal information and account settings"
      icon={User}
    >
      {/* Avatar Upload */}
      <div>
        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-3">
          Profile Picture
        </label>
        <AvatarUpload
          currentAvatar={profile.avatar}
          onUpload={handleAvatarUpload}
          onRemove={handleAvatarRemove}
        />
      </div>

      {/* Full Name */}
      <div>
        <label
          htmlFor="fullName"
          className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
        >
          Full Name
        </label>
        <input
          type="text"
          id="fullName"
          value={profile.fullName}
          onChange={(e) => updateProfile({ fullName: e.target.value })}
          className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-yellow-500 focus:ring-yellow-500 sm:text-sm"
          placeholder="Enter your full name"
        />
      </div>

      {/* Email */}
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
        >
          Email Address
        </label>
        <input
          type="email"
          id="email"
          value={profile.email}
          onChange={(e) => updateProfile({ email: e.target.value })}
          className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-yellow-500 focus:ring-yellow-500 sm:text-sm"
          placeholder="your.email@example.com"
        />
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          You'll need to verify your new email if you change it
        </p>
      </div>

      {/* Bio */}
      <div>
        <label
          htmlFor="bio"
          className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
        >
          Bio
        </label>
        <textarea
          id="bio"
          value={profile.bio || ''}
          onChange={(e) => updateProfile({ bio: e.target.value })}
          rows={3}
          maxLength={500}
          className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-yellow-500 focus:ring-yellow-500 sm:text-sm"
          placeholder="Tell us a bit about yourself..."
        />
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          {(profile.bio || '').length}/500 characters
        </p>
      </div>

      {/* Preferred Language */}
      <Select
        id="preferredLanguage"
        label="Preferred Language"
        value={profile.preferredLanguage}
        onChange={(value) => updateProfile({ preferredLanguage: value as LanguageInterface })}
        options={LANGUAGE_OPTIONS}
      />

      {/* Timezone */}
      <Select
        id="timezone"
        label="Timezone"
        value={profile.timezone}
        onChange={(value) => updateProfile({ timezone: value })}
        options={TIMEZONE_OPTIONS}
      />

      {/* Date Format */}
      <Select
        id="dateFormat"
        label="Date Format"
        value={profile.dateFormat}
        onChange={(value) => updateProfile({ dateFormat: value as DateFormat })}
        options={DATE_FORMAT_OPTIONS}
      />
    </PreferenceCard>
  )
}
