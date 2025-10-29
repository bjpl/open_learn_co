'use client'

/**
 * Loading Skeleton Components
 * Provides visual placeholders while real data loads
 */

export function ArticleCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm animate-pulse">
      <div className="flex items-center space-x-4 mb-3">
        <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
      </div>
      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
      <div className="h-6 w-3/4 bg-gray-200 dark:bg-gray-700 rounded mb-3"></div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
      <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
      <div className="flex items-center justify-between">
        <div className="flex space-x-3">
          <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
        <div className="h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>
  )
}

export function StatCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
          <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
        <div className="h-12 w-12 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
      </div>
    </div>
  )
}

export function SourceCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="h-5 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
      </div>
      <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
    </div>
  )
}

export function TrendingListSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-start space-x-3 p-3 animate-pulse">
          <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
          <div className="flex-1">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div className="h-3 w-3/4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function AnalyticsCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm animate-pulse">
      <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg mb-3"></div>
      <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
      <div className="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
      <div className="h-3 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
    </div>
  )
}

export function CategoryBarSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
          <div className="w-24 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      ))}
    </div>
  )
}

export function FullPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
        <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
        <div className="h-4 w-96 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>
      <div className="grid gap-6">
        <ArticleCardSkeleton />
        <ArticleCardSkeleton />
        <ArticleCardSkeleton />
      </div>
    </div>
  )
}
