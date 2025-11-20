/**
 * FilterPanel Component
 * Main filter container with collapsible sections
 */

'use client';

import { useState } from 'react';
import { useFilters } from '@/lib/filters/filter-hooks';
import { DateRangeFilter } from './DateRangeFilter';
import { SourceFilter } from './SourceFilter';
import { CategoryFilter } from './CategoryFilter';
import { SentimentFilter } from './SentimentFilter';
import { DifficultyFilter } from './DifficultyFilter';
import { SearchFilter } from './SearchFilter';
import { FilterTag } from '@/components/ui/FilterTag';

interface FilterPanelProps {
  className?: string;
  onClose?: () => void;
  showSearch?: boolean;
}

export function FilterPanel({ className = '', onClose, showSearch = true }: FilterPanelProps) {
  const { filters, activeCount, activeLabels, clearFilters, clearFilter } = useFilters();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['date', 'sources', 'categories'])
  );

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  return (
    <aside className={`bg-white border-r border-gray-200 h-full flex flex-col ${className}`} aria-label="Article filters">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-2 hover:bg-gray-100 rounded-md"
              aria-label="Close filters"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Active filter count and clear button */}
        {activeCount > 0 && (
          <div className="flex items-center justify-between" role="status" aria-live="polite">
            <span className="text-sm text-gray-600">
              {activeCount} filter{activeCount > 1 ? 's' : ''} active
            </span>
            <button
              onClick={clearFilters}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              aria-label={`Clear all ${activeCount} active filters`}
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Active filter tags */}
      {activeLabels.length > 0 && (
        <div className="p-4 border-b border-gray-200 space-y-2">
          <h3 className="text-xs font-medium text-gray-700 uppercase">Active Filters</h3>
          <div className="flex flex-wrap gap-2" role="list" aria-label="Active filters">
            {activeLabels.map((item) => (
              <FilterTag
                key={item.key}
                label={item.label}
                onRemove={() => clearFilter(item.key as any)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Filter sections */}
      <div className="flex-1 overflow-y-auto">
        {/* Search filter */}
        {showSearch && (
          <div className="p-4 border-b border-gray-200">
            <SearchFilter />
          </div>
        )}

        {/* Date range filter */}
        <FilterSection
          title="Date Range"
          isExpanded={expandedSections.has('date')}
          onToggle={() => toggleSection('date')}
        >
          <DateRangeFilter />
        </FilterSection>

        {/* Source filter */}
        <FilterSection
          title="Sources"
          isExpanded={expandedSections.has('sources')}
          onToggle={() => toggleSection('sources')}
        >
          <SourceFilter />
        </FilterSection>

        {/* Category filter */}
        <FilterSection
          title="Categories"
          isExpanded={expandedSections.has('categories')}
          onToggle={() => toggleSection('categories')}
        >
          <CategoryFilter />
        </FilterSection>

        {/* Sentiment filter */}
        <FilterSection
          title="Sentiment"
          isExpanded={expandedSections.has('sentiment')}
          onToggle={() => toggleSection('sentiment')}
        >
          <SentimentFilter />
        </FilterSection>

        {/* Difficulty filter */}
        <FilterSection
          title="Difficulty Level"
          isExpanded={expandedSections.has('difficulty')}
          onToggle={() => toggleSection('difficulty')}
        >
          <DifficultyFilter />
        </FilterSection>
      </div>
    </div>
  );
}

interface FilterSectionProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function FilterSection({ title, isExpanded, onToggle, children }: FilterSectionProps) {
  const sectionId = `filter-section-${title.toLowerCase().replace(/\s+/g, '-')}`;

  return (
    <div className="border-b border-gray-200">
      <h3>
        <button
          onClick={onToggle}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
          aria-expanded={isExpanded}
          aria-controls={sectionId}
        >
          <span className="font-medium text-gray-900">{title}</span>
          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </h3>
      {isExpanded && (
        <div id={sectionId} className="px-4 py-3" role="region" aria-label={`${title} filters`}>
          {children}
        </div>
      )}
    </div>
  );
}
