'use client'

import { useEffect } from 'react'
import { Providers } from './providers'
import { ErrorBoundary } from '@/components/error-boundary'
import { reportWebVitals, initPerformanceMonitoring } from '@/lib/performance'
import dynamic from 'next/dynamic'
import { logger } from '@/utils/logger'

// Lazy load Navbar for better initial bundle size
const Navbar = dynamic(() => import('@/components/Navbar'), {
  ssr: true,
  loading: () => (
    <div className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 animate-pulse"></div>
  ),
})

function PerformanceMonitor() {
  useEffect(() => {
    // Initialize performance monitoring
    if (process.env.NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING === 'true') {
      initPerformanceMonitoring()

      // Report Web Vitals
      if (typeof window !== 'undefined') {
        import('web-vitals').then(({ onCLS, onFID, onFCP, onLCP, onTTFB }) => {
          onCLS(reportWebVitals)
          onFID(reportWebVitals)
          onFCP(reportWebVitals)
          onLCP(reportWebVitals)
          onTTFB(reportWebVitals)
        })
      }
    }
  }, [])

  return null
}

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        logger.error('[ClientLayout] Application error', {
          error: error.message,
          stack: error.stack,
          componentStack: errorInfo?.componentStack,
        })
      }}
    >
      <Providers>
        {/* Skip Navigation Link for Keyboard Users */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <Navbar />
          <main id="main-content" tabIndex={-1} className="container mx-auto px-4 py-6">
            {children}
          </main>
        </div>
        <PerformanceMonitor />
      </Providers>
    </ErrorBoundary>
  )
}
