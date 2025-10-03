/**
 * SentimentFilter Component
 * Slider and quick buttons for sentiment filtering
 */

'use client';

import { useFilters } from '@/lib/filters/filter-hooks';
import { Slider } from '@/components/ui/Slider';
import { SENTIMENT_OPTIONS } from '@/lib/filters/filter-types';
import { formatSentiment } from '@/lib/filters/filter-utils';

export function SentimentFilter() {
  const { filters, updateFilters } = useFilters();

  const currentMin = filters.sentiment?.min ?? -1;
  const currentMax = filters.sentiment?.max ?? 1;

  const handleSliderChange = (value: [number, number]) => {
    updateFilters({
      sentiment: {
        min: value[0],
        max: value[1],
      },
    });
  };

  const handleQuickOption = (min: number, max: number) => {
    updateFilters({
      sentiment: { min, max },
    });
  };

  return (
    <div className="space-y-4">
      {/* Quick sentiment buttons */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">Quick Options</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => handleQuickOption(-1, -0.3)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Negative
          </button>
          <button
            onClick={() => handleQuickOption(-0.3, 0.3)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Neutral
          </button>
          <button
            onClick={() => handleQuickOption(0.3, 1)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Positive
          </button>
        </div>
      </div>

      {/* Sentiment slider */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Custom Range</label>
        <Slider
          min={-1}
          max={1}
          step={0.1}
          value={[currentMin, currentMax]}
          onChange={handleSliderChange}
          formatLabel={formatSentiment}
        />
      </div>

      {/* Sentiment scale indicator */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Very Negative</span>
        <span>Neutral</span>
        <span>Very Positive</span>
      </div>
    </div>
  );
}
