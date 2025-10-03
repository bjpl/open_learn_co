/**
 * Privacy Preferences Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'
import { Shield } from 'lucide-react'
import { usePreferences } from '@/lib/preferences/use-preferences'
import { PreferenceCard } from '@/components/ui/PreferenceCard'
import { RadioGroup, RadioOption } from '@/components/ui/RadioGroup'
import { ToggleSwitch } from '@/components/ui/ToggleSwitch'
import type { ProfileVisibility } from '@/lib/preferences/preferences-types'

const PROFILE_VISIBILITY_OPTIONS: RadioOption[] = [
  { value: 'public', label: 'Public', description: 'Your profile is visible to everyone' },
  { value: 'private', label: 'Private', description: 'Only you can see your profile' },
]

export function PrivacyPreferences() {
  const { preferences, updatePrivacy } = usePreferences()

  if (!preferences) return null

  const { privacy } = preferences

  return (
    <PreferenceCard
      title="Privacy & Data"
      description="Control your data and privacy settings"
      icon={Shield}
    >
      <RadioGroup
        name="profileVisibility"
        label="Profile Visibility"
        options={PROFILE_VISIBILITY_OPTIONS}
        value={privacy.profileVisibility}
        onChange={(value) => updatePrivacy({ profileVisibility: value as ProfileVisibility })}
      />

      <ToggleSwitch
        id="shareAnalytics"
        checked={privacy.shareAnalytics}
        onChange={(checked) => updatePrivacy({ shareAnalytics: checked })}
        label="Share Usage Analytics"
        description="Help us improve by sharing anonymous usage data"
      />

      <ToggleSwitch
        id="personalizedRecommendations"
        checked={privacy.personalizedRecommendations}
        onChange={(checked) => updatePrivacy({ personalizedRecommendations: checked })}
        label="Personalized Recommendations"
        description="Receive content recommendations based on your activity"
      />

      <ToggleSwitch
        id="dataCollectionConsent"
        checked={privacy.dataCollectionConsent}
        onChange={(checked) => updatePrivacy({ dataCollectionConsent: checked })}
        label="Data Collection Consent"
        description="Allow collection of learning data to improve your experience"
      />

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          We respect your privacy and follow GDPR guidelines.
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Read our{' '}
          <a href="/privacy" className="text-yellow-600 hover:text-yellow-700 underline">
            Privacy Policy
          </a>
          {' '}to learn more about how we protect your data.
        </p>
      </div>
    </PreferenceCard>
  )
}
