'use client'

import { useState } from 'react'
import { Filter } from 'lucide-react'
import { RouteErrorBoundary } from '@/components/error-boundary'
import { FilterPanel } from '@/components/filters/FilterPanel'
import { SortControl } from '@/components/filters/SortControl'
import { useFilters } from '@/lib/filters/filter-hooks'

export default function AnalyticsPage() {
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const { activeCount } = useFilters()

  return (
    <RouteErrorBoundary>
      <div className="flex gap-6">
        {/* Desktop Filter Panel */}
        <aside className="hidden lg:block w-80 flex-shrink-0">
          <div className="sticky top-6">
            <FilterPanel showSearch={false} />
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Analytics</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Deep analytics and insights from Colombian data
            </p>
          </div>

          {/* Mobile Filter Button and Sort Controls */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <button
                onClick={() => setIsFilterOpen(true)}
                className="lg:hidden flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
              >
                <Filter className="w-4 h-4" />
                Filters
                {activeCount > 0 && (
                  <span className="bg-white text-yellow-600 px-2 py-0.5 rounded-full text-xs font-bold">
                    {activeCount}
                  </span>
                )}
              </button>

              <div className="flex-1 lg:flex-none">
                <SortControl />
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
            <h2 className="text-xl font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
              Analytics Dashboard Coming Soon
            </h2>
            <p className="text-yellow-700 dark:text-yellow-300">
              Advanced analytics features including predictive models, correlation analysis, and custom reports will be available here.
            </p>
          </div>
        </div>
      </div>

      {/* Mobile Filter Drawer */}
      {isFilterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setIsFilterOpen(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-white dark:bg-gray-800">
            <FilterPanel onClose={() => setIsFilterOpen(false)} showSearch={false} />
          </div>
        </div>
      )}
    </RouteErrorBoundary>
  )
}