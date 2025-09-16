'use client'

import { Database, Globe, Newspaper, Building2, Cloud, Shield, Activity, CheckCircle } from 'lucide-react'

const dataSources = {
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
  return (
    <div className="space-y-8">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Data Sources</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Integrated data sources providing real-time Colombian information
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Total Sources" value="22" icon={Database} />
        <StatCard label="Active Sources" value="20" icon={CheckCircle} />
        <StatCard label="APIs" value="9" icon={Globe} />
        <StatCard label="Scrapers" value="13" icon={Newspaper} />
      </div>

      {/* Sources by Category */}
      {Object.entries(dataSources).map(([category, sources]) => (
        <div key={category}>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {category}
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {sources.map((source) => (
              <SourceCard key={source.name} {...source} />
            ))}
          </div>
        </div>
      ))}
    </div>
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

function SourceCard({
  name,
  description,
  status,
  type,
  dataTypes,
  lastSync,
  icon: Icon,
}: {
  name: string
  description: string
  status: string
  type: string
  dataTypes: string[]
  lastSync: string
  icon: any
}) {
  const getStatusColor = () => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
      case 'maintenance': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <Icon className="w-6 h-6 text-yellow-600 dark:text-yellow-500" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
          {status}
        </span>
      </div>

      <div className="space-y-2">
        <div className="flex items-center text-sm">
          <span className="text-gray-500 dark:text-gray-400 w-20">Type:</span>
          <span className="text-gray-900 dark:text-white font-medium">{type}</span>
        </div>
        <div className="flex items-start text-sm">
          <span className="text-gray-500 dark:text-gray-400 w-20">Data:</span>
          <div className="flex flex-wrap gap-1">
            {dataTypes.map((dataType) => (
              <span
                key={dataType}
                className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-700 dark:text-gray-300"
              >
                {dataType}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center text-sm">
          <span className="text-gray-500 dark:text-gray-400 w-20">Last sync:</span>
          <span className="text-gray-900 dark:text-white">{lastSync}</span>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <button className="text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300 font-medium">
          View Details →
        </button>
        <Activity className="w-4 h-4 text-green-500 animate-pulse" />
      </div>
    </div>
  )
}