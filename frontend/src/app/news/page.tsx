'use client'

import { useState, useEffect } from 'react'
import { Clock, ExternalLink, Tag, TrendingUp, Filter, Database } from 'lucide-react'
import { RouteErrorBoundary } from '@/components/error-boundary'
import { FilterPanel } from '@/components/filters/FilterPanel'
import { SortControl } from '@/components/filters/SortControl'
import { useFilters } from '@/lib/filters/filter-hooks'
import ArticleDetail from '@/components/ArticleDetail'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

// NO MOCK DATA - All articles fetched from real backend API

export default function NewsPage() {
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const { activeCount } = useFilters()
  const [newsItems, setNewsItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState<any | null>(null)

  useEffect(() => {
    // Fetch real articles from backend
    const fetchArticles = async () => {
      try {
        const response = await fetch(`${API_URL}/api/scraping/content/simple?limit=50`)
        const data = await response.json()
        setNewsItems(data.items || [])
      } catch (error) {
        console.error('Failed to fetch articles:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchArticles()
  }, [])

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

          {/* News Grid - REAL DATA */}
          <div className="grid gap-6">
            {loading ? (
              <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-sm text-center">
                <Database className="w-12 h-12 mx-auto mb-4 text-yellow-500 animate-pulse" />
                <p className="text-gray-500 dark:text-gray-400">Loading real articles from database...</p>
              </div>
            ) : newsItems.length > 0 ? (
              newsItems.map((item) => (
                <NewsCard
                  key={item.id}
                  article={item}
                  onClick={() => setSelectedArticle(item)}
                />
              ))
            ) : (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
                <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
                  No articles found
                </h3>
                <p className="text-yellow-700 dark:text-yellow-300">
                  Run scrapers to populate content: POST {API_URL}/api/scraping/trigger/El%20Tiempo
                </p>
              </div>
            )}
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

      {/* Article Detail Modal */}
      <ArticleDetail
        article={selectedArticle}
        isOpen={!!selectedArticle}
        onClose={() => setSelectedArticle(null)}
      />
    </RouteErrorBoundary>
  )
}

function NewsCard({ article, onClick }: { article: any; onClick: () => void }) {
  // Calculate time ago from published_date
  const getTimeAgo = (dateString: string) => {
    if (!dateString) return 'Unknown'
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 60) return `${diffMins} minutes ago`
    if (diffHours < 24) return `${diffHours} hours ago`
    if (diffDays < 7) return `${diffDays} days ago`
    return date.toLocaleDateString()
  }

  // Determine if article is trending (high difficulty = more complex/important)
  const isTrending = article.difficulty_score >= 4.5

  return (
    <div
      className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-4 mb-2 flex-wrap">
            <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
              {article.source}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              {getTimeAgo(article.published_date)}
            </span>
            {isTrending && (
              <span className="text-xs bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-2 py-1 rounded-full flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                Trending
              </span>
            )}
            <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded-full">
              {article.word_count || 0} words
            </span>
          </div>

          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2 hover:text-yellow-600 dark:hover:text-yellow-400">
            {article.title}
          </h3>

          {article.subtitle && (
            <p className="text-gray-600 dark:text-gray-300 mb-2 text-sm italic">
              {article.subtitle}
            </p>
          )}

          <p className="text-gray-600 dark:text-gray-300 mb-4 line-clamp-3">
            {article.content || 'No preview available'}
          </p>

          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-4 flex-wrap gap-2">
              <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                <Tag className="w-3 h-3 mr-1" />
                {article.category || 'News'}
              </span>
              {article.author && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  By {article.author}
                </span>
              )}
              {article.tags && article.tags.length > 0 && (
                <div className="flex gap-1">
                  {article.tags.slice(0, 3).map((tag: string, i: number) => (
                    <span key={i} className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation()
                onClick()
              }}
              className="flex items-center text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300 font-medium"
            >
              Read more →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}