/**
 * SourceFilter Component
 * Multi-select filter for article sources with dynamic loading from API
 */

'use client';

import { useFilters } from '@/lib/filters/filter-hooks';
import { MultiSelect } from '@/components/ui/MultiSelect';
import { FilterOption } from '@/lib/filters/filter-types';
import { useState, useEffect } from 'react';
import { logger } from '@/utils/logger';

export function SourceFilter() {
  const { filters, updateFilters } = useFilters();
  const [sources, setSources] = useState<FilterOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch sources from API on mount
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await fetch('/api/v1/sources?format=ui');
        if (response.ok) {
          const data = await response.json();

          // API already returns proper format with value, label, disabled
          const sourceOptions: FilterOption[] = data.sources.map((source: any) => ({
            value: source.value || source.name,
            label: source.label || source.name,
            disabled: !source.active || !source.scraper_available
          }));

          setSources(sourceOptions);
        } else {
          // Fallback to hardcoded list if API fails
          setSources(getDefaultSources());
        }
      } catch (error) {
        logger.error('Failed to fetch sources', error);
        // Fallback to hardcoded list
        setSources(getDefaultSources());
      } finally {
        setIsLoading(false);
      }
    };

    fetchSources();
  }, []);

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
      </div>
    );
  }

  return (
    <MultiSelect
      options={sources}
      selected={filters.sources || []}
      onChange={(sources) => updateFilters({ sources })}
      placeholder="All sources"
    />
  );
}

// Fallback sources if API is unavailable
function getDefaultSources(): FilterOption[] {
  return [
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
  ];
}
