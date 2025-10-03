# Filtering System - Quick Start Guide

## 🚀 Quick Start

### 1. Add Filtering to a Page

```tsx
'use client'

import { useState } from 'react'
import { FilterPanel } from '@/components/filters/FilterPanel'
import { SortControl } from '@/components/filters/SortControl'
import { useFilters } from '@/lib/filters/filter-hooks'

export default function MyPage() {
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const { filters, sort, activeCount } = useFilters()

  return (
    <div className="flex gap-6">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-80">
        <FilterPanel />
      </aside>

      {/* Main Content */}
      <div className="flex-1">
        {/* Mobile Filter Button */}
        <button onClick={() => setIsFilterOpen(true)} className="lg:hidden">
          Filters ({activeCount})
        </button>

        {/* Sort Control */}
        <SortControl />

        {/* Your content here */}
      </div>

      {/* Mobile Drawer */}
      {isFilterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setIsFilterOpen(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-white">
            <FilterPanel onClose={() => setIsFilterOpen(false)} />
          </div>
        </div>
      )}
    </div>
  )
}
```

### 2. Use Filters in API Calls

```tsx
import { useFilters } from '@/lib/filters/filter-hooks'
import { buildApiQueryParams } from '@/lib/filters/filter-state'

const { filters, sort } = useFilters()

// Build query params
const queryParams = buildApiQueryParams(filters, sort, page, pageSize)

// Make API call
const response = await fetch(`/api/articles?${new URLSearchParams(queryParams)}`)
```

### 3. Access Filter State

```tsx
const {
  filters,         // { dateRange, sources, categories, sentiment, difficulty, search }
  sort,            // { field: 'date', direction: 'desc' }
  activeCount,     // Number of active filters
  activeLabels,    // [{ key: 'sources', label: 'Sources: El Tiempo', value: [...] }]
  updateFilters,   // (updates: Partial<ArticleFilters>) => void
  updateSort,      // (sort: SortConfig) => void
  clearFilters,    // () => void
  clearFilter,     // (key: keyof ArticleFilters) => void
  setFilters,      // (filters: ArticleFilters, sort?: SortConfig) => void
} = useFilters()
```

## 🎯 Common Use Cases

### Update a Single Filter

```tsx
const { updateFilters } = useFilters()

// Update sources
updateFilters({ sources: ['eltiempo', 'semana'] })

// Update date range
updateFilters({
  dateRange: {
    from: new Date('2024-01-01'),
    to: new Date()
  }
})
```

### Clear Specific Filter

```tsx
const { clearFilter } = useFilters()

clearFilter('sources')      // Clear sources filter
clearFilter('dateRange')    // Clear date range
clearFilter('sentiment')    // Clear sentiment
```

### Load Filter Preset

```tsx
import { DEFAULT_PRESETS } from '@/lib/filters/filter-types'
const { setFilters } = useFilters()

// Load "Latest News" preset
const preset = DEFAULT_PRESETS.find(p => p.id === 'latest-news')
if (preset) {
  setFilters(preset.filters, preset.sort)
}
```

### Custom Filter Combinations

```tsx
// Easy positive news from this week
updateFilters({
  dateRange: {
    from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    to: new Date(),
  },
  difficulty: ['A1', 'A2', 'B1'],
  sentiment: { min: 0.5, max: 1.0 },
})
```

## 📊 Filter Types Reference

### Date Range
```tsx
dateRange: {
  from?: Date,
  to?: Date
}
```

### Sources
```tsx
sources: ['eltiempo', 'semana', 'elespectador']
```

### Categories
```tsx
categories: ['politics', 'economy', 'technology']
```

### Sentiment
```tsx
sentiment: {
  min: -1.0,  // Very negative
  max: 1.0    // Very positive
}
```

### Difficulty
```tsx
difficulty: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
```

### Search
```tsx
search: 'your search term'
```

## 🔧 Customization

### Hide Search in Filter Panel

```tsx
<FilterPanel showSearch={false} />
```

### Custom Sort Options

```tsx
// See src/components/filters/SortControl.tsx
// Modify SORT_OPTIONS array to add/remove options
```

### Add Custom Filter Preset

```tsx
import { saveFilterPreset } from '@/lib/filters/filter-state'

saveFilterPreset(
  'My Custom Filter',
  {
    categories: ['technology'],
    difficulty: ['C1', 'C2'],
  },
  { field: 'date', direction: 'desc' }
)
```

## 🎨 Styling

All components use Tailwind CSS classes. Key customization points:

### Filter Panel Width
```tsx
<aside className="w-80">  {/* Change width here */}
  <FilterPanel />
</aside>
```

### Mobile Breakpoint
```tsx
{/* Change lg: to md: or xl: as needed */}
<aside className="hidden lg:block w-80">
```

### Active Filter Badge Color
```tsx
{/* In FilterPanel.tsx */}
className="bg-blue-100 text-blue-800"  {/* Change colors */}
```

## 🐛 Troubleshooting

### Filters Not Persisting
**Issue**: Filters reset on page change
**Solution**: Ensure you're using `useFilters()` hook which reads from URL

### Mobile Drawer Not Showing
**Issue**: Drawer doesn't appear on mobile
**Solution**: Check z-index is 50+ and overlay is present

### Debounce Not Working
**Issue**: Search updates too fast
**Solution**: Verify debounce utility is imported and used

### URL Too Long
**Issue**: URL becomes too long with many filters
**Solution**: Consider using filter preset IDs instead of full filter state

## 📱 Responsive Breakpoints

- `sm`: 640px (Mobile)
- `md`: 768px (Tablet)
- `lg`: 1024px (Desktop) - **Default filter sidebar breakpoint**
- `xl`: 1280px (Large Desktop)

## ⌨️ Keyboard Shortcuts

- `Tab`: Navigate between filters
- `Enter`: Toggle checkbox/select option
- `Escape`: Close filter drawer/dropdown
- `Arrow Keys`: Navigate dropdown options
- `Space`: Toggle checkbox

## 🔗 Related Files

- **Components**: `src/components/filters/`
- **UI Library**: `src/components/ui/`
- **Utilities**: `src/lib/filters/`
- **Types**: `src/lib/filters/filter-types.ts`
- **Documentation**: `src/lib/filters/README.md`

## 💡 Tips

1. **URL State**: Filters are stored in URL, making them shareable
2. **Debouncing**: Search is debounced by 300ms automatically
3. **Performance**: Filters use React.memo where appropriate
4. **Accessibility**: All components are keyboard-navigable
5. **Mobile First**: Designed for mobile, enhanced for desktop

## 🆘 Need Help?

- **Documentation**: See `src/lib/filters/README.md`
- **Examples**: Check `src/app/news/page.tsx`
- **Types**: Reference `src/lib/filters/filter-types.ts`
- **Issues**: Create a GitHub issue with `filter` label

---

**Quick Links**:
- [Full Documentation](./src/lib/filters/README.md)
- [Implementation Summary](./docs/phase3-filtering-implementation.md)
- [Backend API Integration](./docs/backend-api.md)
