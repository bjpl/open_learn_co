/**
 * DateRangeFilter Component
 * Date range picker for filtering articles by publication date
 */

'use client';

import { useFilters } from '@/lib/filters/filter-hooks';
import { DatePicker } from '@/components/ui/DatePicker';

export function DateRangeFilter() {
  const { filters, updateFilters } = useFilters();

  return (
    <DatePicker
      value={filters.dateRange}
      onChange={(dateRange) => updateFilters({ dateRange })}
    />
  );
}
