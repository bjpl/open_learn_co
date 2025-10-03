/**
 * FilterTag Component
 * Active filter chip with remove button
 */

'use client';

interface FilterTagProps {
  label: string;
  onRemove: () => void;
  className?: string;
}

export function FilterTag({ label, onRemove, className = '' }: FilterTagProps) {
  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm ${className}`}
    >
      <span>{label}</span>
      <button
        type="button"
        onClick={onRemove}
        className="hover:bg-blue-200 rounded-full p-0.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label={`Remove ${label} filter`}
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}
