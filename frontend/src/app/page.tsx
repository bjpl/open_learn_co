'use client'

import { useState, useEffect } from 'react'
import { Activity, TrendingUp, Users, FileText, Database } from 'lucide-react'
import StatsCard from '@/components/StatsCard'
import SourceStatus from '@/components/SourceStatus'
import { RouteErrorBoundary, ComponentErrorBoundary } from '@/components/error-boundary'
import ArticleDetail from '@/components/ArticleDetail'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

// NO MOCK DATA - All data fetched from real backend API

export default function Dashboard() {
  const [articleCount, setArticleCount] = useState<number>(0)
  const [recentArticles, setRecentArticles] = useState<any[]>([])
  const [sourceStats, setSourceStats] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState<any | null>(null)

  useEffect(() => {
    // Fetch real data from API
    const fetchData = async () => {
      try {
        // Get articles
        const articlesResponse = await fetch(`${API_URL}/api/v1/scraping/content/simple?limit=20`)
        const articlesData = await articlesResponse.json()
        setRecentArticles(articlesData.items || [])
        setArticleCount(articlesData.count || 0)

        // Get source statistics from articles
        const sourceMap = new Map<string, number>()
        articlesData.items?.forEach((article: any) => {
          const count = sourceMap.get(article.source) || 0
          sourceMap.set(article.source, count + 1)
        })
        const stats = Array.from(sourceMap.entries()).map(([name, count]) => ({
          name,
          articles: count,
          status: 'online'
        }))
        setSourceStats(stats)
      } catch (error) {
        logger.error('Failed to fetch articles', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  return (
    <RouteErrorBoundary>
      <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-yellow-500 to-orange-600 rounded-lg p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Colombian Data Intelligence Dashboard</h1>
        <p className="text-yellow-100 text-lg">
          Real-time insights from {sourceStats.length} active sources • {articleCount} articles in database
        </p>
      </div>

      {/* Stats Grid - REAL DATA ONLY */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Articles"
          value={articleCount.toString()}
          change={0}
          icon={FileText}
          trend="neutral"
        />
        <StatsCard
          title="Active Sources"
          value={sourceStats.length.toString()}
          change={0}
          icon={Database}
          trend="neutral"
        />
        <StatsCard
          title="Avg Words/Article"
          value={recentArticles.length > 0
            ? Math.round(recentArticles.reduce((sum, a) => sum + (a.word_count || 0), 0) / recentArticles.length).toString()
            : "0"}
          change={0}
          icon={FileText}
          trend="neutral"
        />
        <StatsCard
          title="Latest Update"
          value={recentArticles[0]?.published_date
            ? new Date(recentArticles[0].published_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            : "N/A"}
          change={0}
          icon={Activity}
          trend="neutral"
        />
      </div>

      {/* Source Status Grid - REAL DATA */}
      <ComponentErrorBoundary>
        <div>
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Data Sources ({sourceStats.length} active)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <SourceStatus sources={sourceStats} />
          </div>
        </div>
      </ComponentErrorBoundary>

      {/* Recent Activity Feed - REAL DATA */}
      <ComponentErrorBoundary>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Recent Articles from Database</h3>
          {loading ? (
            <div className="text-gray-500 dark:text-gray-400">Loading real data...</div>
          ) : recentArticles.length > 0 ? (
            <div className="space-y-3">
              {recentArticles.map((article, index) => (
                <ActivityItem
                  key={article.id || index}
                  type="news"
                  title={`${article.source}: ${article.title}`}
                  time={article.published_date ? new Date(article.published_date).toLocaleString() : 'Unknown'}
                  subtitle={article.subtitle}
                  onClick={() => setSelectedArticle(article)}
                />
              ))}
            </div>
          ) : (
            <div className="text-yellow-600 dark:text-yellow-400 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <p className="font-semibold">No articles in database yet!</p>
              <p className="text-sm mt-2">Run scraper to populate: POST {API_URL}/api/scraping/trigger/El%20Tiempo</p>
            </div>
          )}
        </div>
      </ComponentErrorBoundary>

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

function ActivityItem({ type, title, time, subtitle, onClick }: { type: string; title: string; time: string; subtitle?: string; onClick?: () => void }) {
  const getIcon = () => {
    switch(type) {
      case 'news': return <FileText className="w-4 h-4" />
      case 'api': return <Database className="w-4 h-4" />
      case 'analysis': return <TrendingUp className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getColor = () => {
    switch(type) {
      case 'news': return 'text-blue-500'
      case 'api': return 'text-green-500'
      case 'analysis': return 'text-purple-500'
      default: return 'text-gray-500'
    }
  }

  return (
    <div
      className="flex items-start space-x-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className={`mt-0.5 ${getColor()}`}>
        {getIcon()}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900 dark:text-white hover:text-yellow-600 dark:hover:text-yellow-400">
          {title}
        </p>
        {subtitle && <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">{subtitle}</p>}
        <p className="text-xs text-gray-500 dark:text-gray-400">{time}</p>
      </div>
    </div>
  )
}