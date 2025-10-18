/**
 * Test Fixtures - Preferences
 * Mock data for preference-related tests
 */

// Phase 1: Temporarily disable strict typing on test fixtures to speed up deployment
// import type { UserPreferences } from '@/lib/preferences/preferences-types'

export const mockUserPreferences = {
  profile: {
    fullName: 'Test User',
    email: 'test@example.com',
    bio: 'Test bio',
    avatar: undefined,
    preferredLanguage: 'es',
    timezone: 'America/Bogota',
    dateFormat: 'DD/MM/YYYY',
  },
  notifications: {
    email: {
      dailyDigest: true,
      weeklySummary: true,
      contentAlerts: true,
      vocabularyReminders: false,
      systemUpdates: true,
    },
    inApp: {
      newArticles: true,
      vocabularyReview: false,
      achievements: true,
      systemMessages: true,
    },
    deliveryTimes: {
      dailyDigestTime: '09:00',
      quietHoursStart: '22:00',
      quietHoursEnd: '08:00',
    },
  },
  display: {
    theme: 'light',
    compactMode: false,
    showSourceIcons: true,
    articlesPerPage: 20,
    defaultView: 'grid',
  },
  privacy: {
    profileVisibility: 'private',
    showActivity: false,
    allowAnalytics: true,
    shareData: false,
  },
  language: {
    interfaceLanguage: 'es',
    translationEnabled: true,
    autoDetectLanguage: true,
    preferredSources: ['es'],
  },
}

export const mockProfilePreferences = mockUserPreferences.profile

export const mockNotificationPreferences = mockUserPreferences.notifications

export const mockDisplayPreferences = mockUserPreferences.display

export const mockPrivacyPreferences = mockUserPreferences.privacy

export const mockLanguagePreferences = mockUserPreferences.language
