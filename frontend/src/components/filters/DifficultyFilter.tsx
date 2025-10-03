/**
 * DifficultyFilter Component
 * CEFR level selection for language difficulty
 */

'use client';

import { useFilters } from '@/lib/filters/filter-hooks';
import { CEFR_LEVELS, CEFRLevel } from '@/lib/filters/filter-types';
import { toggleArrayValue } from '@/lib/filters/filter-utils';

export function DifficultyFilter() {
  const { filters, updateFilters } = useFilters();

  const handleToggle = (level: CEFRLevel) => {
    const newDifficulty = toggleArrayValue(filters.difficulty, level);
    updateFilters({ difficulty: newDifficulty });
  };

  const handleQuickSelect = (levels: CEFRLevel[]) => {
    updateFilters({ difficulty: levels });
  };

  return (
    <div className="space-y-4">
      {/* Quick select buttons */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">Quick Select</label>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleQuickSelect(['A1', 'A2', 'B1'])}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Beginner - Intermediate
          </button>
          <button
            onClick={() => handleQuickSelect(['B2', 'C1', 'C2'])}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Advanced
          </button>
        </div>
      </div>

      {/* CEFR level grid */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Levels</label>
        <div className="grid grid-cols-3 gap-2">
          {CEFR_LEVELS.map((level) => (
            <button
              key={level.value}
              onClick={() => handleToggle(level.value)}
              className={`px-3 py-2 border rounded-md text-sm font-medium transition-colors ${
                filters.difficulty?.includes(level.value)
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
              title={level.description}
            >
              {level.label}
            </button>
          ))}
        </div>
      </div>

      {/* Level descriptions */}
      <div className="text-xs text-gray-500 space-y-1">
        {CEFR_LEVELS.filter((l) => filters.difficulty?.includes(l.value)).map((level) => (
          <div key={level.value}>
            <span className="font-medium">{level.label}:</span> {level.description}
          </div>
        ))}
      </div>
    </div>
  );
}
