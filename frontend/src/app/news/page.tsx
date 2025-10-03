'use client'

import { useState } from 'react'
import { Clock, ExternalLink, Tag, TrendingUp, Filter } from 'lucide-react'
import { RouteErrorBoundary } from '@/components/error-boundary'
import { FilterPanel } from '@/components/filters/FilterPanel'
import { SortControl } from '@/components/filters/SortControl'
import { useFilters } from '@/lib/filters/filter-hooks'

const newsItems = [
  {
    id: 1,
    title: 'Colombian Economy Shows Signs of Recovery Amid Global Uncertainty',
    source: 'El Tiempo',
    category: 'Economy',
    time: '2 hours ago',
    summary: 'Recent data from DANE shows positive indicators in key economic sectors, suggesting a gradual recovery despite international challenges.',
    sentiment: 'positive',
    trending: true,
  },
  {
    id: 2,
    title: 'New Infrastructure Projects Announced for Pacific Region',
    source: 'La República',
    category: 'Infrastructure',
    time: '3 hours ago',
    summary: 'Government announces major investment in road and port infrastructure to boost connectivity and trade in the Pacific region.',
    sentiment: 'positive',
    trending: false,
  },
  {
    id: 3,
    title: 'Technology Sector Creates 5000 New Jobs in Bogotá',
    source: 'Portafolio',
    category: 'Technology',
    time: '4 hours ago',
    summary: 'Tech companies expand operations in the capital, creating thousands of new opportunities for software developers and IT professionals.',
    sentiment: 'positive',
    trending: true,
  },
  {
    id: 4,
    title: 'Environmental Concerns Rise Over Deforestation Rates',
    source: 'El Espectador',
    category: 'Environment',
    time: '5 hours ago',
    summary: 'IDEAM reports concerning deforestation levels in the Amazon region, prompting calls for stronger environmental protection measures.',
    sentiment: 'negative',
    trending: false,
  },
  {
    id: 5,
    title: 'Education Reform Bill Passes First Congressional Debate',
    source: 'Semana',
    category: 'Education',
    time: '6 hours ago',
    summary: 'Proposed education reforms aimed at improving quality and access move forward in Congress with broad political support.',
    sentiment: 'neutral',
    trending: true,
  },
  {
    id: 6,
    title: 'Central Bank Maintains Interest Rates Amid Inflation Concerns',
    source: 'Dinero',
    category: 'Finance',
    time: '7 hours ago',
    summary: 'Banco de la República decides to keep interest rates unchanged, balancing inflation control with economic growth objectives.',
    sentiment: 'neutral',
    trending: false,
  },
]

export default function NewsPage() {
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const { activeCount } = useFilters()

  return (
    <RouteErrorBoundary>
      <div className="flex gap-6">
        {/* Desktop Filter Panel */}
        <aside className="hidden lg:block w-80 flex-shrink-0">
          <div className="sticky top-6">
            <FilterPanel />
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 space-y-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">News Feed</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Real-time news aggregation from Colombian media sources
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

          {/* News Grid */}
          <div className="grid gap-6">
            {newsItems.map((item) => (
              <NewsCard key={item.id} {...item} />
            ))}
          </div>
        </div>
      </div>

      {/* Mobile Filter Drawer */}
      {isFilterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setIsFilterOpen(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-white dark:bg-gray-800">
            <FilterPanel onClose={() => setIsFilterOpen(false)} />
          </div>
        </div>
      )}
    </RouteErrorBoundary>
  )
}

function NewsCard({
  title,
  source,
  category,
  time,
  summary,
  sentiment,
  trending,
}: {
  title: string
  source: string
  category: string
  time: string
  summary: string
  sentiment: string
  trending: boolean
}) {
  const getSentimentColor = () => {
    switch (sentiment) {
      case 'positive': return 'text-green-500'
      case 'negative': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-4 mb-2">
            <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
              {source}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              {time}
            </span>
            {trending && (
              <span className="text-xs bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-2 py-1 rounded-full flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                Trending
              </span>
            )}
          </div>

          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2 hover:text-yellow-600 dark:hover:text-yellow-400 cursor-pointer">
            {title}
          </h3>

          <p className="text-gray-600 dark:text-gray-300 mb-4">
            {summary}
          </p>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                <Tag className="w-3 h-3 mr-1" />
                {category}
              </span>
              <span className={`text-sm font-medium ${getSentimentColor()}`}>
                Sentiment: {sentiment}
              </span>
            </div>

            <button className="flex items-center text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300">
              Read more
              <ExternalLink className="w-3 h-3 ml-1" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}