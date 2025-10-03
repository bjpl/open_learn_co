/**
 * MultiSelect Component
 * Multi-select dropdown with search
 */

'use client';

import { useState, useMemo } from 'react';
import { FilterOption } from '@/lib/filters/filter-types';
import { filterOptions } from '@/lib/filters/filter-utils';

interface MultiSelectProps {
  options: FilterOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  className?: string;
}

export function MultiSelect({
  options,
  selected,
  onChange,
  placeholder = 'Select options',
  searchPlaceholder = 'Search...',
  className = '',
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  const filteredOptions = useMemo(() => {
    return filterOptions(options, search);
  }, [options, search]);

  const handleToggle = (value: string) => {
    const newSelected = selected.includes(value)
      ? selected.filter((v) => v !== value)
      : [...selected, value];
    onChange(newSelected);
  };

  const handleSelectAll = () => {
    onChange(filteredOptions.map((opt) => opt.value));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const selectedLabels = useMemo(() => {
    return options
      .filter((opt) => selected.includes(opt.value))
      .map((opt) => opt.label)
      .join(', ');
  }, [options, selected]);

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 text-left border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <span className="block truncate">
          {selected.length > 0 ? selectedLabels : placeholder}
        </span>
        {selected.length > 0 && (
          <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">
            {selected.length}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-hidden">
            <div className="p-2 border-b border-gray-200">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={searchPlaceholder}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-2 p-2 border-b border-gray-200">
              <button
                type="button"
                onClick={handleSelectAll}
                className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
              >
                Select All
              </button>
              <button
                type="button"
                onClick={handleClearAll}
                className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded"
              >
                Clear All
              </button>
            </div>

            <div className="overflow-y-auto max-h-64">
              {filteredOptions.length === 0 ? (
                <div className="p-4 text-center text-gray-500">No options found</div>
              ) : (
                filteredOptions.map((option) => (
                  <label
                    key={option.value}
                    className="flex items-center px-4 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selected.includes(option.value)}
                      onChange={() => handleToggle(option.value)}
                      className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="flex-1">{option.label}</span>
                    {option.count !== undefined && (
                      <span className="text-sm text-gray-500">({option.count})</span>
                    )}
                  </label>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
