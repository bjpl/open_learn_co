/**
 * DatePicker Component
 * Date range picker with quick options
 */

'use client';

import { useState } from 'react';
import { DateRange, QUICK_DATE_OPTIONS } from '@/lib/filters/filter-types';

interface DatePickerProps {
  value?: DateRange;
  onChange: (range: DateRange) => void;
  className?: string;
}

export function DatePicker({ value, onChange, className = '' }: DatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);

  const formatDate = (date?: Date) => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  };

  const handleQuickOption = (option: typeof QUICK_DATE_OPTIONS[0]) => {
    onChange(option.getValue());
    setIsOpen(false);
  };

  const handleFromChange = (dateStr: string) => {
    onChange({
      ...value,
      from: dateStr ? new Date(dateStr) : undefined,
    });
  };

  const handleToChange = (dateStr: string) => {
    onChange({
      ...value,
      to: dateStr ? new Date(dateStr) : undefined,
    });
  };

  const handleClear = () => {
    onChange({});
  };

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 text-left border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {value?.from || value?.to ? (
          <span>
            {formatDate(value.from) || '...'} - {formatDate(value.to) || '...'}
          </span>
        ) : (
          <span className="text-gray-500">Select date range</span>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg p-4">
            <div className="space-y-4">
              {/* Quick options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quick Options
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {QUICK_DATE_OPTIONS.map((option) => (
                    <button
                      key={option.label}
                      type="button"
                      onClick={() => handleQuickOption(option)}
                      className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Custom Range
                </label>
                <div className="space-y-2">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">From</label>
                    <input
                      type="date"
                      value={formatDate(value?.from)}
                      onChange={(e) => handleFromChange(e.target.value)}
                      max={formatDate(new Date())}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">To</label>
                    <input
                      type="date"
                      value={formatDate(value?.to)}
                      onChange={(e) => handleToChange(e.target.value)}
                      max={formatDate(new Date())}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleClear}
                className="w-full px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Clear
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
