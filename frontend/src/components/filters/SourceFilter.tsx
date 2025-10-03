/**
 * SourceFilter Component
 * Multi-select filter for article sources
 */

'use client';

import { useFilters } from '@/lib/filters/filter-hooks';
import { MultiSelect } from '@/components/ui/MultiSelect';

// TODO: Fetch from API
const SOURCE_OPTIONS = [
  { value: 'eltiempo', label: 'El Tiempo' },
  { value: 'semana', label: 'Semana' },
  { value: 'elespectador', label: 'El Espectador' },
  { value: 'portafolio', label: 'Portafolio' },
  { value: 'larepublica', label: 'La República' },
  { value: 'elheraldo', label: 'El Heraldo' },
  { value: 'elpais', label: 'El País' },
  { value: 'elcolombiano', label: 'El Colombiano' },
  { value: 'caracol', label: 'Caracol Radio' },
  { value: 'rcn', label: 'RCN Radio' },
];

export function SourceFilter() {
  const { filters, updateFilters } = useFilters();

  return (
    <MultiSelect
      options={SOURCE_OPTIONS}
      selected={filters.sources || []}
      onChange={(sources) => updateFilters({ sources })}
      placeholder="All sources"
      searchPlaceholder="Search sources..."
    />
  );
}
