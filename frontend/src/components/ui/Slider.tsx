/**
 * Slider Component
 * Range slider for sentiment filtering
 */

'use client';

import { useState, useEffect } from 'react';

interface SliderProps {
  min: number;
  max: number;
  step?: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
  formatLabel?: (value: number) => string;
  className?: string;
}

export function Slider({
  min,
  max,
  step = 0.1,
  value,
  onChange,
  formatLabel = (v) => v.toFixed(1),
  className = '',
}: SliderProps) {
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMin = parseFloat(e.target.value);
    const newValue: [number, number] = [Math.min(newMin, localValue[1]), localValue[1]];
    setLocalValue(newValue);
    onChange(newValue);
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMax = parseFloat(e.target.value);
    const newValue: [number, number] = [localValue[0], Math.max(newMax, localValue[0])];
    setLocalValue(newValue);
    onChange(newValue);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex justify-between text-sm text-gray-600">
        <span>{formatLabel(localValue[0])}</span>
        <span>{formatLabel(localValue[1])}</span>
      </div>

      <div className="space-y-2">
        {/* Min slider */}
        <div>
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={localValue[0]}
            onChange={handleMinChange}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        {/* Max slider */}
        <div>
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={localValue[1]}
            onChange={handleMaxChange}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>
      </div>

      {/* Value inputs */}
      <div className="flex gap-2">
        <input
          type="number"
          min={min}
          max={localValue[1]}
          step={step}
          value={localValue[0]}
          onChange={(e) => {
            const newValue: [number, number] = [
              Math.max(min, Math.min(parseFloat(e.target.value) || min, localValue[1])),
              localValue[1],
            ];
            setLocalValue(newValue);
            onChange(newValue);
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="number"
          min={localValue[0]}
          max={max}
          step={step}
          value={localValue[1]}
          onChange={(e) => {
            const newValue: [number, number] = [
              localValue[0],
              Math.max(localValue[0], Math.min(parseFloat(e.target.value) || max, max)),
            ];
            setLocalValue(newValue);
            onChange(newValue);
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>
  );
}
