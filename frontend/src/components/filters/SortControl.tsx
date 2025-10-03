/**
 * SortControl Component
 * Sort dropdown with direction toggle
 */

'use client';

import { useFilters } from '@/lib/filters/filter-hooks';
import { SortField, SortDirection } from '@/lib/filters/filter-types';

const SORT_OPTIONS: Array<{ value: SortField; label: string }> = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'date', label: 'Date' },
  { value: 'sentiment', label: 'Sentiment' },
  { value: 'source', label: 'Source' },
  { value: 'difficulty', label: 'Difficulty' },
];

export function SortControl() {
  const { sort, updateSort } = useFilters();

  const currentField = sort?.field || 'date';
  const currentDirection = sort?.direction || 'desc';

  const handleFieldChange = (field: SortField) => {
    updateSort({ field, direction: currentDirection });
  };

  const handleDirectionToggle = () => {
    const newDirection: SortDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    updateSort({ field: currentField, direction: newDirection });
  };

  const getDirectionIcon = () => {
    if (currentDirection === 'asc') {
      return (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  const getDirectionLabel = () => {
    switch (currentField) {
      case 'date':
        return currentDirection === 'desc' ? 'Newest first' : 'Oldest first';
      case 'sentiment':
        return currentDirection === 'desc' ? 'Most positive' : 'Most negative';
      case 'difficulty':
        return currentDirection === 'desc' ? 'Hardest first' : 'Easiest first';
      case 'source':
        return currentDirection === 'desc' ? 'Z to A' : 'A to Z';
      default:
        return currentDirection === 'desc' ? 'Descending' : 'Ascending';
    }
  };

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="sort-select" className="text-sm font-medium text-gray-700">
        Sort by:
      </label>
      <select
        id="sort-select"
        value={currentField}
        onChange={(e) => handleFieldChange(e.target.value as SortField)}
        className="px-3 py-2 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <button
        onClick={handleDirectionToggle}
        className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        title={getDirectionLabel()}
        aria-label={`Toggle sort direction: ${getDirectionLabel()}`}
      >
        {getDirectionIcon()}
      </button>
    </div>
  );
}
