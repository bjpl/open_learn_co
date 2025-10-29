'use client'

import { useState, useEffect } from 'react'
import { Database, Newspaper, Activity, CheckCircle, AlertCircle, Play } from 'lucide-react'
import { RouteErrorBoundary, ComponentErrorBoundary } from '@/components/error-boundary'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

// Available scrapers configuration (what can be run)
const availableScrapers = [
  { name: 'El Tiempo', description: 'Colombia\'s largest newspaper', endpoint: 'El%20Tiempo' },
  { name: 'El Espectador', description: 'National daily newspaper', endpoint: 'El%20Espectador' },
  { name: 'Semana', description: 'Weekly news magazine', endpoint: 'Semana' },
  { name: 'Portafolio', description: 'Business and financial newspaper', endpoint: 'Portafolio' },
]

// Informational sources (not yet implemented)
const plannedSources = {
  'Government APIs': [
    {
      name: 'DANE',
      description: 'National Administrative Department of Statistics',
      status: 'active',
      type: 'API',
      dataTypes: ['Demographics', 'Economy', 'Social Indicators'],
      lastSync: '5 minutes ago',
      icon: Building2,
    },
    {
      name: 'Banco de la República',
      description: 'Central Bank of Colombia',
      status: 'active',
      type: 'API',
      dataTypes: ['Monetary Policy', 'Exchange Rates', 'Inflation'],
      lastSync: '10 minutes ago',
      icon: Building2,
    },
    {
      name: 'SECOP',
      description: 'Public Procurement System',
      status: 'maintenance',
      type: 'API',
      dataTypes: ['Government Contracts', 'Public Spending'],
      lastSync: '2 hours ago',
      icon: Shield,
    },
    {
      name: 'IDEAM',
      description: 'Institute of Hydrology, Meteorology and Environmental Studies',
      status: 'active',
      type: 'API',
      dataTypes: ['Weather', 'Climate', 'Environmental Data'],
      lastSync: '15 minutes ago',
      icon: Cloud,
    },
  ],
  'News Media': [
    {
      name: 'El Tiempo',
      description: 'Colombia\'s largest newspaper',
      status: 'active',
      type: 'Scraper',
      dataTypes: ['News', 'Politics', 'Economy'],
      lastSync: '2 minutes ago',
      icon: Newspaper,
    },
    {
      name: 'El Espectador',
      description: 'National daily newspaper',
      status: 'active',
      type: 'Scraper',
      dataTypes: ['News', 'Opinion', 'Analysis'],
      lastSync: '8 minutes ago',
      icon: Newspaper,
    },
    {
      name: 'Semana',
      description: 'Weekly news magazine',
      status: 'active',
      type: 'Scraper',
      dataTypes: ['Politics', 'Investigation', 'Analysis'],
      lastSync: '12 minutes ago',
      icon: Newspaper,
    },
    {
      name: 'La República',
      description: 'Business and financial newspaper',
      status: 'active',
      type: 'Scraper',
      dataTypes: ['Business', 'Finance', 'Markets'],
      lastSync: '15 minutes ago',
      icon: Newspaper,
    },
  ],
  'Open Data Portals': [
    {
      name: 'Datos.gov.co',
      description: 'Colombian Open Data Portal',
      status: 'active',
      type: 'API',
      dataTypes: ['Multiple Datasets', 'Public Information'],
      lastSync: '30 minutes ago',
      icon: Database,
    },
    {
      name: 'DNP',
      description: 'National Planning Department',
      status: 'active',
      type: 'API',
      dataTypes: ['Development Plans', 'Public Investment'],
      lastSync: '1 hour ago',
      icon: Building2,
    },
  ],
}

export default function SourcesPage() {
  const [sourceStats, setSourceStats] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState<string | null>(null)

  useEffect(() => {
    fetchSourceStats()
  }, [])

  const fetchSourceStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/scraping/content/simple?limit=100`)
      const data = await response.json()
      const items = data.items || []

      // Calculate stats per source
      const sourceMap = new Map<string, any>()
      items.forEach((article: any) => {
        const existing = sourceMap.get(article.source) || {
          name: article.source,
          articleCount: 0,
          totalWords: 0,
          avgDifficulty: 0,
          lastUpdate: article.published_date
        }
        existing.articleCount++
        existing.totalWords += article.word_count || 0
        existing.avgDifficulty += article.difficulty_score || 0
        if (new Date(article.published_date) > new Date(existing.lastUpdate)) {
          existing.lastUpdate = article.published_date
        }
        sourceMap.set(article.source, existing)
      })

      const stats = Array.from(sourceMap.values()).map(stat => ({
        ...stat,
        avgWords: Math.round(stat.totalWords / stat.articleCount),
        avgDifficulty: (stat.avgDifficulty / stat.articleCount).toFixed(2)
      }))

      setSourceStats(stats)
    } catch (error) {
      console.error('Failed to fetch source stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const triggerScraper = async (endpoint: string, name: string) => {
    setTriggering(name)
    try {
      await fetch(`${API_URL}/api/scraping/trigger/${endpoint}`, { method: 'POST' })
      setTimeout(() => {
        fetchSourceStats()
        setTriggering(null)
      }, 2000)
    } catch (error) {
      console.error(`Failed to trigger ${name}:`, error)
      setTriggering(null)
    }
  }

  return (
    <RouteErrorBoundary>
      <div className="space-y-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Data Sources</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Active scrapers and data sources for Colombian content
          </p>
        </div>

        {/* Real Statistics from Database */}
        <ComponentErrorBoundary>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              label="Active Scrapers"
              value={sourceStats.length.toString()}
              icon={CheckCircle}
            />
            <StatCard
              label="Total Articles"
              value={sourceStats.reduce((sum, s) => sum + s.articleCount, 0).toString()}
              icon={Database}
            />
            <StatCard
              label="Avg Article Length"
              value={sourceStats.length > 0
                ? Math.round(sourceStats.reduce((sum, s) => sum + s.avgWords, 0) / sourceStats.length).toString()
                : '0'}
              icon={Newspaper}
            />
            <StatCard
              label="Avg Complexity"
              value={sourceStats.length > 0
                ? (sourceStats.reduce((sum, s) => sum + parseFloat(s.avgDifficulty), 0) / sourceStats.length).toFixed(2)
                : '0.0'}
              icon={Activity}
            />
          </div>
        </ComponentErrorBoundary>

        {/* Active Scrapers with Real Data */}
        <ComponentErrorBoundary>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Active News Scrapers ({sourceStats.length})
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {availableScrapers.map((scraper) => {
                const stats = sourceStats.find(s => s.name === scraper.name)
                const isActive = !!stats
                return (
                  <ActiveScraperCard
                    key={scraper.name}
                    {...scraper}
                    stats={stats}
                    isActive={isActive}
                    onTrigger={() => triggerScraper(scraper.endpoint, scraper.name)}
                    isTriggering={triggering === scraper.name}
                  />
                )
              })}
            </div>
          </div>
        </ComponentErrorBoundary>

        {/* Planned Sources (Informational) */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Planned Integrations (Coming Soon)
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(plannedSources).map(([category, sources]: [string, any]) => (
              <div key={category} className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">{category}</h3>
                <div className="space-y-1">
                  {sources.map((source: any) => (
                    <div key={source.name} className="text-sm text-gray-600 dark:text-gray-400">
                      • {source.name}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </RouteErrorBoundary>
  )
}

function StatCard({ label, value, icon: Icon }: { label: string; value: string; icon: any }) {
  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        </div>
        <Icon className="w-8 h-8 text-yellow-500" />
      </div>
    </div>
  )
}

function ActiveScraperCard({
  name,
  description,
  endpoint,
  stats,
  isActive,
  onTrigger,
  isTriggering
}: {
  name: string
  description: string
  endpoint: string
  stats?: any
  isActive: boolean
  onTrigger: () => void
  isTriggering: boolean
}) {
  const getTimeAgo = (dateString: string) => {
    if (!dateString) return 'Never'
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow border-2 border-transparent hover:border-yellow-500">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <Newspaper className="w-6 h-6 text-yellow-600 dark:text-yellow-500" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
          </div>
        </div>
        {isActive ? (
          <div className="flex items-center space-x-1">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-xs text-green-600 dark:text-green-400 font-medium">Active</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1">
            <AlertCircle className="w-5 h-5 text-gray-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Inactive</span>
          </div>
        )}
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-4 mb-4 p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg">
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Articles</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white">{stats.articleCount}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Avg Words</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white">{stats.avgWords}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Avg Difficulty</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white">{stats.avgDifficulty}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Last Update</p>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{getTimeAgo(stats.lastUpdate)}</p>
          </div>
        </div>
      )}

      <button
        onClick={onTrigger}
        disabled={isTriggering}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isTriggering ? (
          <>
            <Activity className="w-4 h-4 animate-spin" />
            Running scraper...
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            Run Scraper
          </>
        )}
      </button>
    </div>
  )
}