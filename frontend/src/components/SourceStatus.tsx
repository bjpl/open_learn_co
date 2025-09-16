'use client'

import { CheckCircle, AlertCircle, XCircle } from 'lucide-react'

const sources = [
  { name: 'El Tiempo', status: 'online', lastUpdate: '2 min ago', articles: 342 },
  { name: 'DANE API', status: 'online', lastUpdate: '5 min ago', articles: 1250 },
  { name: 'El Espectador', status: 'online', lastUpdate: '8 min ago', articles: 289 },
  { name: 'Banco República', status: 'warning', lastUpdate: '45 min ago', articles: 156 },
  { name: 'Semana', status: 'online', lastUpdate: '12 min ago', articles: 198 },
  { name: 'SECOP API', status: 'offline', lastUpdate: '2 hours ago', articles: 0 },
  { name: 'La República', status: 'online', lastUpdate: '15 min ago', articles: 167 },
  { name: 'Portafolio', status: 'online', lastUpdate: '18 min ago', articles: 134 },
  { name: 'IDEAM', status: 'online', lastUpdate: '22 min ago', articles: 89 },
]

export default function SourceStatus() {
  return (
    <>
      {sources.map((source) => (
        <div
          key={source.name}
          className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 dark:text-white">{source.name}</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Last update: {source.lastUpdate}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                {source.articles} articles today
              </p>
            </div>
            <StatusIcon status={source.status} />
          </div>
        </div>
      ))}
    </>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'online':
      return (
        <div className="flex items-center space-x-1">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <span className="text-xs text-green-600 dark:text-green-400">Online</span>
        </div>
      )
    case 'warning':
      return (
        <div className="flex items-center space-x-1">
          <AlertCircle className="w-5 h-5 text-yellow-500" />
          <span className="text-xs text-yellow-600 dark:text-yellow-400">Slow</span>
        </div>
      )
    case 'offline':
      return (
        <div className="flex items-center space-x-1">
          <XCircle className="w-5 h-5 text-red-500" />
          <span className="text-xs text-red-600 dark:text-red-400">Offline</span>
        </div>
      )
    default:
      return null
  }
}