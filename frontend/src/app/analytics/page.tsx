'use client'

import { useState, useEffect } from 'react'
import { Filter, BarChart3, PieChart, TrendingUp, FileText, Calendar, Award } from 'lucide-react'
import { RouteErrorBoundary, ComponentErrorBoundary } from '@/components/error-boundary'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

// NO MOCK DATA - Real analytics from database

export default function AnalyticsPage() {
  const [articles, setArticles] = useState<any[]>([])
  const [analytics, setAnalytics] = useState({
    totalArticles: 0,
    avgWordCount: 0,
    avgDifficulty: 0,
    totalWords: 0,
    categoryBreakdown: [] as {category: string, count: number}[],
    difficultyDistribution: [] as {level: string, count: number}[],
    dateRange: { oldest: '', newest: '' }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch(`${API_URL}/api/scraping/content/simple?limit=100`)
        const data = await response.json()
        const items = data.items || []
        setArticles(items)

        if (items.length === 0) {
          setLoading(false)
          return
        }

        // Calculate analytics
        const totalWords = items.reduce((sum: number, a: any) => sum + (a.word_count || 0), 0)
        const avgWords = Math.round(totalWords / items.length)
        const avgDiff = items.reduce((sum: number, a: any) => sum + (a.difficulty_score || 0), 0) / items.length

        // Category breakdown
        const categoryMap = new Map<string, number>()
        items.forEach((article: any) => {
          const cat = article.category || 'Uncategorized'
          categoryMap.set(cat, (categoryMap.get(cat) || 0) + 1)
        })
        const categories = Array.from(categoryMap.entries())
          .map(([category, count]) => ({category, count}))
          .sort((a, b) => b.count - a.count)

        // Difficulty distribution
        const difficultyRanges = [
          { level: 'Easy (1-2)', min: 0, max: 2, count: 0 },
          { level: 'Medium (2-3.5)', min: 2, max: 3.5, count: 0 },
          { level: 'Hard (3.5-4.5)', min: 3.5, max: 4.5, count: 0 },
          { level: 'Expert (4.5-5)', min: 4.5, max: 5.1, count: 0 }
        ]
        items.forEach((article: any) => {
          const score = article.difficulty_score || 0
          difficultyRanges.forEach(range => {
            if (score >= range.min && score < range.max) {
              range.count++
            }
          })
        })

        // Date range
        const dates = items.map((a: any) => new Date(a.published_date)).filter(d => !isNaN(d.getTime()))
        const oldest = dates.length > 0 ? new Date(Math.min(...dates.map(d => d.getTime()))) : null
        const newest = dates.length > 0 ? new Date(Math.max(...dates.map(d => d.getTime()))) : null

        setAnalytics({
          totalArticles: items.length,
          avgWordCount: avgWords,
          avgDifficulty: avgDiff,
          totalWords: totalWords,
          categoryBreakdown: categories,
          difficultyDistribution: difficultyRanges.filter(r => r.count > 0),
          dateRange: {
            oldest: oldest ? oldest.toLocaleDateString() : 'N/A',
            newest: newest ? newest.toLocaleDateString() : 'N/A'
          }
        })

      } catch (error) {
        console.error('Failed to fetch analytics:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchAnalytics()
  }, [])

  return (
    <RouteErrorBoundary>
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Analytics Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time analytics from {analytics.totalArticles} Colombian articles
          </p>
        </div>

        {loading ? (
          <div className="bg-white dark:bg-gray-800 p-12 rounded-lg shadow-sm text-center">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-yellow-500 animate-pulse" />
            <p className="text-gray-500 dark:text-gray-400">Calculating analytics...</p>
          </div>
        ) : articles.length === 0 ? (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-8 text-center">
            <h2 className="text-xl font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
              No data available for analysis
            </h2>
            <p className="text-yellow-700 dark:text-yellow-300">
              Run scrapers to populate content and see analytics.
            </p>
          </div>
        ) : (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <ComponentErrorBoundary>
                <MetricCard
                  icon={FileText}
                  label="Total Articles"
                  value={analytics.totalArticles.toString()}
                  subtitle={`${analytics.totalWords.toLocaleString()} total words`}
                  color="blue"
                />
              </ComponentErrorBoundary>
              <ComponentErrorBoundary>
                <MetricCard
                  icon={BarChart3}
                  label="Avg Word Count"
                  value={analytics.avgWordCount.toString()}
                  subtitle="words per article"
                  color="green"
                />
              </ComponentErrorBoundary>
              <ComponentErrorBoundary>
                <MetricCard
                  icon={Award}
                  label="Avg Difficulty"
                  value={analytics.avgDifficulty.toFixed(2)}
                  subtitle="out of 5.0"
                  color="purple"
                />
              </ComponentErrorBoundary>
              <ComponentErrorBoundary>
                <MetricCard
                  icon={Calendar}
                  label="Date Range"
                  value={analytics.dateRange.newest}
                  subtitle={`From ${analytics.dateRange.oldest}`}
                  color="orange"
                />
              </ComponentErrorBoundary>
            </div>

            {/* Category Breakdown */}
            <ComponentErrorBoundary>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <PieChart className="w-5 h-5 mr-2 text-yellow-500" />
                  Articles by Category
                </h2>
                {analytics.categoryBreakdown.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.categoryBreakdown.map(({category, count}) => (
                      <div key={category} className="flex items-center gap-3">
                        <div className="w-32 text-sm text-gray-700 dark:text-gray-300 font-medium">
                          {category}
                        </div>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3 relative overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-yellow-400 to-orange-500 h-3 rounded-full transition-all duration-500"
                            style={{width: `${(count / analytics.totalArticles) * 100}%`}}
                          />
                        </div>
                        <div className="w-24 text-right">
                          <span className="text-sm font-bold text-gray-900 dark:text-white">{count}</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
                            ({((count / analytics.totalArticles) * 100).toFixed(1)}%)
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400 text-center py-8">No category data available</p>
                )}
              </div>
            </ComponentErrorBoundary>

            {/* Difficulty Distribution */}
            <ComponentErrorBoundary>
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2 text-purple-500" />
                  Reading Difficulty Distribution
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {analytics.difficultyDistribution.map(({level, count}) => (
                    <div key={level} className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 p-4 rounded-lg text-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{level}</p>
                      <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{count}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {((count / analytics.totalArticles) * 100).toFixed(0)}% of articles
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </ComponentErrorBoundary>
          </>
        )}
      </div>
    </RouteErrorBoundary>
  )
}

function MetricCard({ icon: Icon, label, value, subtitle, color }: {
  icon: any
  label: string
  value: string
  subtitle: string
  color: string
}) {
  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
    orange: 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400',
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-3 ${colorClasses[color as keyof typeof colorClasses]}`}>
        <Icon className="w-6 h-6" />
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{value}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
    </div>
  )
}