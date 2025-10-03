/**
 * Display Preferences Component
 * OpenLearn Colombia - Phase 3
 */

'use client'

import React from 'react'
import { Monitor } from 'lucide-react'
import { usePreferences } from '@/lib/preferences/use-preferences'
import { PreferenceCard } from '@/components/ui/PreferenceCard'
import { RadioGroup, RadioOption } from '@/components/ui/RadioGroup'
import { Select, SelectOption } from '@/components/ui/Select'
import { ToggleSwitch } from '@/components/ui/ToggleSwitch'
import type { Theme, ColorScheme, FontSize, ContentDensity, DefaultPage, SidebarPosition } from '@/lib/preferences/preferences-types'

const THEME_OPTIONS: RadioOption[] = [
  { value: 'light', label: 'Light', description: 'Use light theme' },
  { value: 'dark', label: 'Dark', description: 'Use dark theme' },
  { value: 'auto', label: 'Auto', description: 'Match system settings' },
]

const COLOR_SCHEME_OPTIONS: RadioOption[] = [
  { value: 'default', label: 'Default (Yellow/Orange)' },
  { value: 'blue', label: 'Blue' },
  { value: 'green', label: 'Green' },
  { value: 'purple', label: 'Purple' },
]

const FONT_SIZE_OPTIONS: RadioOption[] = [
  { value: 'small', label: 'Small' },
  { value: 'medium', label: 'Medium' },
  { value: 'large', label: 'Large' },
  { value: 'xlarge', label: 'Extra Large' },
]

const CONTENT_DENSITY_OPTIONS: RadioOption[] = [
  { value: 'comfortable', label: 'Comfortable', description: 'More spacing between elements' },
  { value: 'compact', label: 'Compact', description: 'Fit more content on screen' },
]

const DEFAULT_PAGE_OPTIONS: SelectOption[] = [
  { value: 'dashboard', label: 'Dashboard' },
  { value: 'news', label: 'News' },
  { value: 'vocabulary', label: 'Vocabulary' },
  { value: 'analytics', label: 'Analytics' },
]

const ARTICLES_PER_PAGE_OPTIONS: SelectOption[] = [
  { value: '10', label: '10 articles' },
  { value: '25', label: '25 articles' },
  { value: '50', label: '50 articles' },
  { value: '100', label: '100 articles' },
]

const SIDEBAR_POSITION_OPTIONS: RadioOption[] = [
  { value: 'left', label: 'Left' },
  { value: 'right', label: 'Right' },
  { value: 'hidden', label: 'Hidden' },
]

export function DisplayPreferences() {
  const { preferences, updateAppearance, updateLayout } = usePreferences()

  if (!preferences) return null

  const { display } = preferences

  return (
    <div className="space-y-6">
      {/* Appearance */}
      <PreferenceCard
        title="Appearance"
        description="Customize how the platform looks"
        icon={Monitor}
      >
        <RadioGroup
          name="theme"
          label="Theme"
          options={THEME_OPTIONS}
          value={display.appearance.theme}
          onChange={(value) => updateAppearance({ theme: value as Theme })}
        />

        <RadioGroup
          name="colorScheme"
          label="Color Scheme"
          options={COLOR_SCHEME_OPTIONS}
          value={display.appearance.colorScheme}
          onChange={(value) => updateAppearance({ colorScheme: value as ColorScheme })}
          orientation="horizontal"
        />

        <RadioGroup
          name="fontSize"
          label="Font Size"
          options={FONT_SIZE_OPTIONS}
          value={display.appearance.fontSize}
          onChange={(value) => updateAppearance({ fontSize: value as FontSize })}
          orientation="horizontal"
        />

        <RadioGroup
          name="contentDensity"
          label="Content Density"
          options={CONTENT_DENSITY_OPTIONS}
          value={display.appearance.contentDensity}
          onChange={(value) => updateAppearance({ contentDensity: value as ContentDensity })}
        />
      </PreferenceCard>

      {/* Layout */}
      <PreferenceCard
        title="Layout"
        description="Configure page layout and navigation"
        icon={Monitor}
      >
        <Select
          id="defaultPage"
          label="Default Page"
          value={display.layout.defaultPage}
          onChange={(value) => updateLayout({ defaultPage: value as DefaultPage })}
          options={DEFAULT_PAGE_OPTIONS}
        />

        <Select
          id="articlesPerPage"
          label="Articles Per Page"
          value={display.layout.articlesPerPage.toString()}
          onChange={(value) => updateLayout({ articlesPerPage: parseInt(value, 10) })}
          options={ARTICLES_PER_PAGE_OPTIONS}
        />

        <ToggleSwitch
          id="showImages"
          checked={display.layout.showImages}
          onChange={(checked) => updateLayout({ showImages: checked })}
          label="Show Images in Articles"
          description="Display article thumbnail images"
        />

        <RadioGroup
          name="sidebarPosition"
          label="Sidebar Position"
          options={SIDEBAR_POSITION_OPTIONS}
          value={display.layout.sidebarPosition}
          onChange={(value) => updateLayout({ sidebarPosition: value as SidebarPosition })}
          orientation="horizontal"
        />
      </PreferenceCard>
    </div>
  )
}
