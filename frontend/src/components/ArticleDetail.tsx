'use client'

import { X, ExternalLink, Calendar, User, Hash, FileText, TrendingUp, BookOpen } from 'lucide-react'
import { ComponentErrorBoundary } from './error-boundary'

interface Article {
  id: number
  source: string
  source_url: string
  category: string
  title: string
  subtitle?: string
  content: string
  author?: string
  word_count: number
  published_date: string
  tags?: string[]
  colombian_entities?: string[]
  difficulty_score: number
}

interface ArticleDetailProps {
  article: Article | null
  isOpen: boolean
  onClose: () => void
}

export default function ArticleDetail({ article, isOpen, onClose }: ArticleDetailProps) {
  if (!isOpen || !article) return null

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown date'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getDifficultyLabel = (score: number) => {
    if (score < 2) return { label: 'Easy', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' }
    if (score < 3.5) return { label: 'Medium', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' }
    if (score < 4.5) return { label: 'Hard', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400' }
    return { label: 'Expert', color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' }
  }

  const difficulty = getDifficultyLabel(article.difficulty_score || 0)

  return (
    <ComponentErrorBoundary>
      <div className="fixed inset-0 z-50 overflow-y-auto">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative w-full max-w-4xl bg-white dark:bg-gray-800 rounded-lg shadow-xl transform transition-all">
            {/* Header */}
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between rounded-t-lg">
              <div className="flex items-center space-x-3">
                <span className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 text-sm font-medium rounded-full">
                  {article.source}
                </span>
                <span className={`px-3 py-1 text-xs font-medium rounded-full ${difficulty.color}`}>
                  {difficulty.label} Read
                </span>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              {/* Title */}
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                {article.title}
              </h1>

              {/* Subtitle */}
              {article.subtitle && (
                <p className="text-lg text-gray-600 dark:text-gray-300 mb-6 italic">
                  {article.subtitle}
                </p>
              )}

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 dark:bg-gray-700/30 rounded-lg">
                <div>
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <Calendar className="w-3 h-3 mr-1" />
                    Published
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatDate(article.published_date)}
                  </div>
                </div>

                {article.author && (
                  <div>
                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
                      <User className="w-3 h-3 mr-1" />
                      Author
                    </div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {article.author}
                    </div>
                  </div>
                )}

                <div>
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <FileText className="w-3 h-3 mr-1" />
                    Word Count
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {article.word_count?.toLocaleString() || 0} words
                  </div>
                </div>

                <div>
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <BookOpen className="w-3 h-3 mr-1" />
                    Reading Time
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    ~{Math.ceil((article.word_count || 0) / 200)} min
                  </div>
                </div>
              </div>

              {/* Tags */}
              {article.tags && article.tags.length > 0 && (
                <div className="mb-6">
                  <div className="flex items-center text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    <Hash className="w-4 h-4 mr-1" />
                    Tags
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {article.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 text-sm rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Colombian Entities */}
              {article.colombian_entities && article.colombian_entities.length > 0 && (
                <div className="mb-6">
                  <div className="flex items-center text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    Key Colombian Entities
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {article.colombian_entities.slice(0, 10).map((entity, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 text-sm rounded-full"
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Main Content */}
              <div className="prose dark:prose-invert max-w-none mb-6">
                <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                  {article.content}
                </div>
              </div>

              {/* Footer Actions */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6 flex items-center justify-between flex-wrap gap-4">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Category: <span className="font-medium text-gray-900 dark:text-white">{article.category || 'News'}</span>
                </div>

                {article.source_url && (
                  <a
                    href={article.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Read Original Article
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </ComponentErrorBoundary>
  )
}
