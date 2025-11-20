'use client'

import { useState, useEffect } from 'react'
import { Clock, ExternalLink, Tag, TrendingUp, Filter, Database } from 'lucide-react'
import { RouteErrorBoundary } from '@/components/error-boundary'
import { FilterPanel } from '@/components/filters/FilterPanel'
import { SortControl } from '@/components/filters/SortControl'
import { useFilters } from '@/lib/filters/filter-hooks'
import ArticleDetail from '@/components/ArticleDetail'
import Pagination from '@/components/Pagination'
import { ArticleCardSkeleton } from '@/components/LoadingSkeletons'
import { logger } from '@/utils/logger'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'
const ITEMS_PER_PAGE = 10

// NO MOCK DATA - All articles fetched from real backend API

export default function NewsPage() {
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const { activeCount } = useFilters()
  const [allArticles, setAllArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState<any | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    // Fetch real articles from backend with server-side pagination
    const fetchArticles = async () => {
      try {
        // Fetch only what we need: 10 items per page instead of 100
        const response = await fetch(`${API_URL}/api/v1/scraping/content/simple?limit=10`)
        const data = await response.json()
        setAllArticles(data.items || [])
      } catch (error) {
        // Use structured logging - automatically handles dev/prod
        logger.error('Failed to fetch articles', error)
      } finally {
        setLoading(false)
      }
    }
    fetchArticles()
  }, [])

  // Paginate articles
  const totalPages = Math.ceil(allArticles.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const newsItems = allArticles.slice(startIndex, startIndex + ITEMS_PER_PAGE)

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <RouteErrorBoundary>
      <div className="flex gap-6">
        {/* Desktop Filter Panel */}
        <aside className="hidden lg:block w-80 flex-shrink-0" aria-label="Filter sidebar">
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
                aria-label={`Open filters${activeCount > 0 ? `, ${activeCount} active` : ''}`}
                className="lg:hidden flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
              >
                <Filter className="w-4 h-4" aria-hidden="true" />
                Filters
                {activeCount > 0 && (
                  <span className="bg-white text-yellow-600 px-2 py-0.5 rounded-full text-xs font-bold" aria-label={`${activeCount} filters active`}>
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
          <section aria-label="News articles" className="space-y-6">
            {loading ? (
              <div className="grid gap-6" role="status" aria-label="Loading articles">
                <ArticleCardSkeleton />
                <ArticleCardSkeleton />
                <ArticleCardSkeleton />
                <ArticleCardSkeleton />
                <ArticleCardSkeleton />
                <span className="sr-only">Loading news articles...</span>
              </div>
            ) : allArticles.length > 0 ? (
              <>
                <div className="grid gap-6">
                  {newsItems.map((item) => (
                    <NewsCard
                      key={item.id}
                      article={item}
                      onClick={() => setSelectedArticle(item)}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    totalItems={allArticles.length}
                    itemsPerPage={ITEMS_PER_PAGE}
                    onPageChange={handlePageChange}
                  />
                )}
              </>
            ) : (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center" role="status">
                <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
                  No articles found
                </h3>
                <p className="text-yellow-700 dark:text-yellow-300">
                  Run scrapers to populate content: POST {API_URL}/api/v1/scraping/trigger/El%20Tiempo
                </p>
              </div>
            )}
          </section>
        </div>
      </div>

      {/* Mobile Filter Drawer */}
      {isFilterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Filters">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setIsFilterOpen(false)} aria-hidden="true" />
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <article
      role="article"
      aria-label={`${article.title} from ${article.source}, published ${getTimeAgo(article.published_date)}`}
      tabIndex={0}
      onKeyDown={handleKeyDown}
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
              <Clock className="w-3 h-3 mr-1" aria-hidden="true" />
              <time dateTime={article.published_date}>{getTimeAgo(article.published_date)}</time>
            </span>
            {isTrending && (
              <span className="text-xs bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-2 py-1 rounded-full flex items-center" role="status">
                <TrendingUp className="w-3 h-3 mr-1" aria-hidden="true" />
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
                <Tag className="w-3 h-3 mr-1" aria-hidden="true" />
                {article.category || 'News'}
              </span>
              {article.author && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  By {article.author}
                </span>
              )}
              {article.tags && article.tags.length > 0 && (
                <div className="flex gap-1" role="list" aria-label="Article tags">
                  {article.tags.slice(0, 3).map((tag: string, i: number) => (
                    <span key={i} className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded" role="listitem">
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
              aria-label={`Read full article: ${article.title}`}
              className="flex items-center text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300 font-medium"
            >
              Read more →
            </button>
          </div>
        </div>
      </div>
    </article>
  )
}
