'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Tag, Hash, Newspaper, BarChart3, Clock } from 'lucide-react'
import { RouteErrorBoundary, ComponentErrorBoundary } from '@/components/error-boundary'
import ArticleDetail from '@/components/ArticleDetail'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

// NO MOCK DATA - Real trending analysis from database

export default function TrendsPage() {
  const [articles, setArticles] = useState<any[]>([])
  const [trendingTags, setTrendingTags] = useState<{tag: string, count: number}[]>([])
  const [trendingEntities, setTrendingEntities] = useState<{entity: string, count: number}[]>([])
  const [sourceDistribution, setSourceDistribution] = useState<{source: string, count: number}[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState<any | null>(null)

  useEffect(() => {
    const fetchTrendingData = async () => {
      try {
        const response = await fetch(`${API_URL}/api/scraping/content/simple?limit=100`)
        const data = await response.json()
        const items = data.items || []
        setArticles(items)

        // Analyze trending tags
        const tagMap = new Map<string, number>()
        items.forEach((article: any) => {
          article.tags?.forEach((tag: string) => {
            tagMap.set(tag, (tagMap.get(tag) || 0) + 1)
          })
        })
        const sortedTags = Array.from(tagMap.entries())
          .map(([tag, count]) => ({tag, count}))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10)
        setTrendingTags(sortedTags)

        // Analyze trending entities
        const entityMap = new Map<string, number>()
        items.forEach((article: any) => {
          article.colombian_entities?.forEach((entity: string) => {
            entityMap.set(entity, (entityMap.get(entity) || 0) + 1)
          })
        })
        const sortedEntities = Array.from(entityMap.entries())
          .map(([entity, count]) => ({entity, count}))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10)
        setTrendingEntities(sortedEntities)

        // Source distribution
        const sourceMap = new Map<string, number>()
        items.forEach((article: any) => {
          sourceMap.set(article.source, (sourceMap.get(article.source) || 0) + 1)
        })
        const sortedSources = Array.from(sourceMap.entries())
          .map(([source, count]) => ({source, count}))
          .sort((a, b) => b.count - a.count)
        setSourceDistribution(sortedSources)

      } catch (error) {
        console.error('Failed to fetch trending data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchTrendingData()
  }, [])

  // Get top trending articles (high difficulty score = complex/important)
  const trendingArticles = articles
    .filter(a => a.difficulty_score >= 4.0)
    .sort((a, b) => b.difficulty_score - a.difficulty_score)
    .slice(0, 5)

  return (
    <RouteErrorBoundary>
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Trending Topics</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time trending analysis from {articles.length} Colombian articles
          </p>
        </div>

        {loading ? (
          <div className="bg-white dark:bg-gray-800 p-12 rounded-lg shadow-sm text-center">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-yellow-500 animate-pulse" />
            <p className="text-gray-500 dark:text-gray-400">Analyzing trending patterns...</p>
          </div>
        ) : articles.length === 0 ? (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
            <h2 className="text-xl font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
              No data available for analysis
            </h2>
            <p className="text-yellow-700 dark:text-yellow-300">
              Run scrapers to populate content and see trending topics.
            </p>
          </div>
        ) : (
          <>
            {/* Trending Articles */}
            <ComponentErrorBoundary>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2 text-red-500" />
                  Top Trending Articles (High Complexity)
                </h2>
                <div className="space-y-3">
                  {trendingArticles.map((article, index) => (
                    <div
                      key={article.id}
                      className="flex items-start space-x-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors cursor-pointer"
                      onClick={() => setSelectedArticle(article)}
                    >
                      <div className="flex-shrink-0 w-8 h-8 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
                        <span className="text-red-600 dark:text-red-400 font-bold text-sm">#{index + 1}</span>
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 dark:text-white text-sm hover:text-yellow-600 dark:hover:text-yellow-400">
                          {article.title}
                        </h3>
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                          <span className="text-yellow-600 dark:text-yellow-400">{article.source}</span>
                          <span>Complexity: {article.difficulty_score.toFixed(1)}/5.0</span>
                          <span>{article.word_count} words</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </ComponentErrorBoundary>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Trending Tags */}
              <ComponentErrorBoundary>
                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <Hash className="w-5 h-5 mr-2 text-blue-500" />
                    Trending Tags
                  </h2>
                  {trendingTags.length > 0 ? (
                    <div className="space-y-2">
                      {trendingTags.map(({tag, count}) => (
                        <div key={tag} className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded">
                          <div className="flex items-center">
                            <Tag className="w-4 h-4 mr-2 text-blue-500" />
                            <span className="text-gray-900 dark:text-white">{tag}</span>
                          </div>
                          <span className="text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                            {count} articles
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400 text-center py-8">No tags found in articles</p>
                  )}
                </div>
              </ComponentErrorBoundary>

              {/* Trending Entities */}
              <ComponentErrorBoundary>
                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-green-500" />
                    Top Colombian Entities
                  </h2>
                  {trendingEntities.length > 0 ? (
                    <div className="space-y-2">
                      {trendingEntities.map(({entity, count}) => (
                        <div key={entity} className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded">
                          <span className="text-gray-900 dark:text-white font-medium">{entity}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{width: `${Math.min(100, (count / trendingEntities[0].count) * 100)}%`}}
                              />
                            </div>
                            <span className="text-sm text-gray-500 dark:text-gray-400 w-12 text-right">
                              {count}x
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400 text-center py-8">No entities extracted yet</p>
                  )}
                </div>
              </ComponentErrorBoundary>
            </div>

            {/* Source Distribution */}
            <ComponentErrorBoundary>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <Newspaper className="w-5 h-5 mr-2 text-yellow-500" />
                  Articles by Source
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {sourceDistribution.map(({source, count}) => (
                    <div key={source} className="bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 p-4 rounded-lg">
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{source}</h3>
                      <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">{count}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {((count / articles.length) * 100).toFixed(1)}% of total
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </ComponentErrorBoundary>

            {/* Recent Trending Articles */}
            <ComponentErrorBoundary>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <Clock className="w-5 h-5 mr-2 text-purple-500" />
                  Latest High-Impact Articles
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {articles.slice(0, 6).map((article) => (
                    <div
                      key={article.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-yellow-500 dark:hover:border-yellow-500 transition-colors cursor-pointer"
                      onClick={() => setSelectedArticle(article)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-xs text-yellow-600 dark:text-yellow-400 font-medium">
                          {article.source}
                        </span>
                        <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">
                          {article.word_count || 0} words
                        </span>
                      </div>
                      <h3 className="font-medium text-gray-900 dark:text-white text-sm line-clamp-2 mb-2 hover:text-yellow-600 dark:hover:text-yellow-400">
                        {article.title}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                        {article.subtitle || article.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </ComponentErrorBoundary>
          </>
        )}

        {/* Article Detail Modal */}
        <ArticleDetail
          article={selectedArticle}
          isOpen={!!selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      </div>
    </RouteErrorBoundary>
  )
}