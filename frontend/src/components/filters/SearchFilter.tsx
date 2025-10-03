/**
 * SearchFilter Component
 * Search input with debouncing and clear button
 */

'use client';

import { useState, useEffect } from 'react';
import { useFilters } from '@/lib/filters/filter-hooks';
import { debounce } from '@/lib/filters/filter-utils';

export function SearchFilter() {
  const { filters, updateFilters } = useFilters();
  const [localSearch, setLocalSearch] = useState(filters.search || '');

  // Update local state when filters change externally
  useEffect(() => {
    setLocalSearch(filters.search || '');
  }, [filters.search]);

  // Debounced update function
  useEffect(() => {
    const debouncedUpdate = debounce((value: string) => {
      updateFilters({ search: value });
    }, 300);

    if (localSearch !== filters.search) {
      debouncedUpdate(localSearch);
    }
  }, [localSearch, filters.search, updateFilters]);

  const handleClear = () => {
    setLocalSearch('');
    updateFilters({ search: '' });
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={localSearch}
          onChange={(e) => setLocalSearch(e.target.value)}
          placeholder="Search articles..."
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        {localSearch && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            aria-label="Clear search"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
