'use client'

import { CheckCircle, Database } from 'lucide-react'

interface Source {
  name: string
  articles: number
  status: string
}

export default function SourceStatus({ sources }: { sources: Source[] }) {
  // ONLY REAL DATA - No mock sources
  if (!sources || sources.length === 0) {
    return (
      <div className="col-span-3 text-center text-gray-500 dark:text-gray-400 p-8">
        No sources found. Run scrapers to populate data.
      </div>
    )
  }

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
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                <Database className="inline w-4 h-4 mr-1" />
                {source.articles} articles in database
              </p>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-xs text-green-600 dark:text-green-400">Active</span>
            </div>
          </div>
        </div>
      ))}
    </>
  )
}