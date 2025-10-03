/**
 * Notification Preferences Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'
import { Bell } from 'lucide-react'
import { usePreferences } from '@/lib/preferences/use-preferences'
import { PreferenceCard } from '@/components/ui/PreferenceCard'
import { ToggleSwitch } from '@/components/ui/ToggleSwitch'

export function NotificationPreferences() {
  const { preferences, updateEmailNotifications, updateInAppNotifications, updateNotifications } = usePreferences()

  if (!preferences) return null

  const { notifications } = preferences

  return (
    <div className="space-y-6">
      {/* Email Notifications */}
      <PreferenceCard
        title="Email Notifications"
        description="Manage what emails you receive from us"
        icon={Bell}
      >
        <ToggleSwitch
          id="dailyDigest"
          checked={notifications.email.dailyDigest}
          onChange={(checked) => updateEmailNotifications({ dailyDigest: checked })}
          label="Daily Digest"
          description="Receive a daily summary of new content and updates"
        />

        <ToggleSwitch
          id="weeklySummary"
          checked={notifications.email.weeklySummary}
          onChange={(checked) => updateEmailNotifications({ weeklySummary: checked })}
          label="Weekly Summary"
          description="Get a weekly roundup of top stories and your progress"
        />

        <ToggleSwitch
          id="contentAlerts"
          checked={notifications.email.contentAlerts}
          onChange={(checked) => updateEmailNotifications({ contentAlerts: checked })}
          label="New Content Alerts"
          description="Be notified when new articles match your interests"
        />

        <ToggleSwitch
          id="vocabularyReminders"
          checked={notifications.email.vocabularyReminders}
          onChange={(checked) => updateEmailNotifications({ vocabularyReminders: checked })}
          label="Vocabulary Reminders"
          description="Get reminders to review your vocabulary"
        />

        <ToggleSwitch
          id="systemUpdates"
          checked={notifications.email.systemUpdates}
          onChange={(checked) => updateEmailNotifications({ systemUpdates: checked })}
          label="System Updates"
          description="Receive important platform updates and announcements"
        />
      </PreferenceCard>

      {/* In-App Notifications */}
      <PreferenceCard
        title="In-App Notifications"
        description="Control notifications within the platform"
        icon={Bell}
      >
        <ToggleSwitch
          id="newArticles"
          checked={notifications.inApp.newArticles}
          onChange={(checked) => updateInAppNotifications({ newArticles: checked })}
          label="New Articles"
          description="Show notifications for articles matching your interests"
        />

        <ToggleSwitch
          id="vocabularyReview"
          checked={notifications.inApp.vocabularyReview}
          onChange={(checked) => updateInAppNotifications({ vocabularyReview: checked })}
          label="Vocabulary Review"
          description="Remind you to review vocabulary words"
        />

        <ToggleSwitch
          id="achievements"
          checked={notifications.inApp.achievements}
          onChange={(checked) => updateInAppNotifications({ achievements: checked })}
          label="Achievements"
          description="Celebrate when you unlock achievements and milestones"
        />

        <ToggleSwitch
          id="systemMessages"
          checked={notifications.inApp.systemMessages}
          onChange={(checked) => updateInAppNotifications({ systemMessages: checked })}
          label="System Messages"
          description="Important system messages and maintenance notifications"
        />
      </PreferenceCard>

      {/* Delivery Times */}
      <PreferenceCard
        title="Delivery Times"
        description="Control when you receive notifications"
        icon={Bell}
      >
        <div>
          <label
            htmlFor="dailyDigestTime"
            className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
          >
            Daily Digest Time
          </label>
          <input
            type="time"
            id="dailyDigestTime"
            value={notifications.deliveryTimes.dailyDigestTime}
            onChange={(e) => updateNotifications({
              deliveryTimes: {
                ...notifications.deliveryTimes,
                dailyDigestTime: e.target.value,
              },
            })}
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-yellow-500 focus:ring-yellow-500 sm:text-sm"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Preferred time to receive your daily digest
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="quietHoursStart"
              className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
            >
              Quiet Hours Start
            </label>
            <input
              type="time"
              id="quietHoursStart"
              value={notifications.deliveryTimes.quietHoursStart}
              onChange={(e) => updateNotifications({
                deliveryTimes: {
                  ...notifications.deliveryTimes,
                  quietHoursStart: e.target.value,
                },
              })}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-yellow-500 focus:ring-yellow-500 sm:text-sm"
            />
          </div>

          <div>
            <label
              htmlFor="quietHoursEnd"
              className="block text-sm font-medium text-gray-900 dark:text-white mb-2"
            >
              Quiet Hours End
            </label>
            <input
              type="time"
              id="quietHoursEnd"
              value={notifications.deliveryTimes.quietHoursEnd}
              onChange={(e) => updateNotifications({
                deliveryTimes: {
                  ...notifications.deliveryTimes,
                  quietHoursEnd: e.target.value,
                },
              })}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-yellow-500 focus:ring-yellow-500 sm:text-sm"
            />
          </div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          No notifications will be sent during quiet hours
        </p>
      </PreferenceCard>
    </div>
  )
}
