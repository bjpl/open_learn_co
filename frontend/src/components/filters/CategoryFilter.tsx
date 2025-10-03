/**
 * CategoryFilter Component
 * Checkbox list for article categories
 */

'use client';

import { useFilters } from '@/lib/filters/filter-hooks';
import { CATEGORY_OPTIONS } from '@/lib/filters/filter-types';
import { Checkbox } from '@/components/ui/Checkbox';
import { toggleArrayValue } from '@/lib/filters/filter-utils';

export function CategoryFilter() {
  const { filters, updateFilters } = useFilters();

  const handleToggle = (category: string) => {
    const newCategories = toggleArrayValue(filters.categories, category);
    updateFilters({ categories: newCategories });
  };

  return (
    <div className="space-y-2">
      {CATEGORY_OPTIONS.map((option) => (
        <Checkbox
          key={option.value}
          id={`category-${option.value}`}
          checked={filters.categories?.includes(option.value) || false}
          onChange={() => handleToggle(option.value)}
          label={option.label}
        />
      ))}
    </div>
  );
}
