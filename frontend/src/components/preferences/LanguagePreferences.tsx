/**
 * Language Learning Preferences Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'
import { GraduationCap } from 'lucide-react'
import { usePreferences } from '@/lib/preferences/use-preferences'
import { PreferenceCard } from '@/components/ui/PreferenceCard'
import { RadioGroup, RadioOption } from '@/components/ui/RadioGroup'
import { Select, SelectOption } from '@/components/ui/Select'
import { ToggleSwitch } from '@/components/ui/ToggleSwitch'
import { MultiSelect } from '@/components/ui/MultiSelect'
import { FilterOption } from '@/lib/filters/filter-types'
import type {
  CEFRLevel,
  ReviewFrequency,
  DifficultyPreference,
  TranslationDisplay,
} from '@/lib/preferences/preferences-types'

const CEFR_LEVEL_OPTIONS: SelectOption[] = [
  { value: 'A1', label: 'A1 - Beginner' },
  { value: 'A2', label: 'A2 - Elementary' },
  { value: 'B1', label: 'B1 - Intermediate' },
  { value: 'B2', label: 'B2 - Upper Intermediate' },
  { value: 'C1', label: 'C1 - Advanced' },
  { value: 'C2', label: 'C2 - Proficient' },
]

const VOCAB_GOAL_OPTIONS: SelectOption[] = [
  { value: '5', label: '5 words per day' },
  { value: '10', label: '10 words per day' },
  { value: '15', label: '15 words per day' },
  { value: '20', label: '20 words per day' },
]

const REVIEW_FREQUENCY_OPTIONS: RadioOption[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'every2days', label: 'Every 2 days' },
  { value: 'weekly', label: 'Weekly' },
]

const DIFFICULTY_OPTIONS: RadioOption[] = [
  { value: 'easy', label: 'Easy', description: 'Comfortable learning pace' },
  { value: 'balanced', label: 'Balanced', description: 'Mix of easy and challenging' },
  { value: 'challenge', label: 'Challenge me', description: 'Push my limits' },
]

const TRANSLATION_OPTIONS: RadioOption[] = [
  { value: 'always', label: 'Always show' },
  { value: 'hover', label: 'Show on hover' },
  { value: 'never', label: 'Never show' },
]

const CONTENT_LENGTH_OPTIONS: RadioOption[] = [
  { value: 'short', label: 'Short (< 5 min)' },
  { value: 'medium', label: 'Medium (5-15 min)' },
  { value: 'long', label: 'Long (15+ min)' },
  { value: 'any', label: 'Any length' },
]

const NEWS_SOURCE_OPTIONS: FilterOption[] = [
  { value: 'El Tiempo', label: 'El Tiempo' },
  { value: 'El Espectador', label: 'El Espectador' },
  { value: 'Semana', label: 'Semana' },
  { value: 'La República', label: 'La República' },
  { value: 'Portafolio', label: 'Portafolio' },
  { value: 'Dinero', label: 'Dinero' },
  { value: 'El Colombiano', label: 'El Colombiano' },
  { value: 'El País', label: 'El País' },
  { value: 'El Heraldo', label: 'El Heraldo' },
  { value: 'El Universal', label: 'El Universal' },
  { value: 'Pulzo', label: 'Pulzo' },
  { value: 'La Silla Vacía', label: 'La Silla Vacía' },
  { value: 'Razón Pública', label: 'Razón Pública' },
  { value: 'La FM', label: 'La FM' },
  { value: 'Blu Radio', label: 'Blu Radio' },
]

const CATEGORY_OPTIONS: FilterOption[] = [
  { value: 'Politics', label: 'Politics' },
  { value: 'Economy', label: 'Economy' },
  { value: 'Business', label: 'Business' },
  { value: 'Technology', label: 'Technology' },
  { value: 'Culture', label: 'Culture' },
  { value: 'Sports', label: 'Sports' },
  { value: 'Environment', label: 'Environment' },
  { value: 'Education', label: 'Education' },
  { value: 'Health', label: 'Health' },
  { value: 'Security', label: 'Security' },
  { value: 'International', label: 'International' },
  { value: 'Regional', label: 'Regional' },
  { value: 'Opinion', label: 'Opinion' },
]

export function LanguagePreferences() {
  const { preferences, updateLearning } = usePreferences()

  if (!preferences) return null

  const { learning } = preferences

  return (
    <div className="space-y-6">
      {/* Learning Level */}
      <PreferenceCard
        title="Learning Level"
        description="Set your current and target proficiency level"
        icon={GraduationCap}
      >
        <div className="grid grid-cols-2 gap-4">
          <Select
            id="currentLevel"
            label="Current Level (CEFR)"
            value={learning.currentLevel}
            onChange={(value) => updateLearning({ currentLevel: value as CEFRLevel })}
            options={CEFR_LEVEL_OPTIONS}
          />

          <Select
            id="targetLevel"
            label="Target Level"
            value={learning.targetLevel}
            onChange={(value) => updateLearning({ targetLevel: value as CEFRLevel })}
            options={CEFR_LEVEL_OPTIONS}
          />
        </div>

        <Select
          id="dailyVocabGoal"
          label="Daily Vocabulary Goal"
          value={learning.dailyVocabGoal.toString()}
          onChange={(value) => updateLearning({ dailyVocabGoal: parseInt(value, 10) })}
          options={VOCAB_GOAL_OPTIONS}
        />

        <RadioGroup
          name="reviewFrequency"
          label="Review Frequency"
          options={REVIEW_FREQUENCY_OPTIONS}
          value={learning.reviewFrequency}
          onChange={(value) => updateLearning({ reviewFrequency: value as ReviewFrequency })}
          orientation="horizontal"
        />
      </PreferenceCard>

      {/* Learning Style */}
      <PreferenceCard
        title="Learning Style"
        description="Customize your learning experience"
        icon={GraduationCap}
      >
        <RadioGroup
          name="difficultyPreference"
          label="Difficulty Preference"
          options={DIFFICULTY_OPTIONS}
          value={learning.difficultyPreference}
          onChange={(value) => updateLearning({ difficultyPreference: value as DifficultyPreference })}
        />

        <RadioGroup
          name="showTranslations"
          label="Translation Display"
          options={TRANSLATION_OPTIONS}
          value={learning.showTranslations}
          onChange={(value) => updateLearning({ showTranslations: value as TranslationDisplay })}
          orientation="horizontal"
        />

        <ToggleSwitch
          id="colombianSpanishFocus"
          checked={learning.colombianSpanishFocus}
          onChange={(checked) => updateLearning({ colombianSpanishFocus: checked })}
          label="Colombian Spanish Focus"
          description="Emphasize Colombian vocabulary and expressions"
        />
      </PreferenceCard>

      {/* Content Preferences */}
      <PreferenceCard
        title="Content Preferences"
        description="Filter and customize your content feed"
        icon={GraduationCap}
      >
        <RadioGroup
          name="contentLength"
          label="Preferred Content Length"
          options={CONTENT_LENGTH_OPTIONS}
          value={learning.contentLengthPreference}
          onChange={(value) => updateLearning({ contentLengthPreference: value as any })}
        />

        <div>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-3">
            Difficulty Range
          </label>
          <div className="space-y-2">
            <input
              type="range"
              min="0"
              max="100"
              value={learning.difficultyRange[0]}
              onChange={(e) => updateLearning({
                difficultyRange: [parseInt(e.target.value, 10), learning.difficultyRange[1]],
              })}
              className="w-full"
            />
            <input
              type="range"
              min="0"
              max="100"
              value={learning.difficultyRange[1]}
              onChange={(e) => updateLearning({
                difficultyRange: [learning.difficultyRange[0], parseInt(e.target.value, 10)],
              })}
              className="w-full"
            />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {learning.difficultyRange[0]}% - {learning.difficultyRange[1]}%
            </p>
          </div>
        </div>

        <MultiSelect
          options={NEWS_SOURCE_OPTIONS}
          selected={learning.preferredSources}
          onChange={(sources) => updateLearning({ preferredSources: sources })}
          placeholder="Select news sources..."
        />

        <MultiSelect
          options={CATEGORY_OPTIONS}
          selected={learning.preferredCategories}
          onChange={(categories) => updateLearning({ preferredCategories: categories })}
          placeholder="Select categories..."
        />
      </PreferenceCard>
    </div>
  )
}
