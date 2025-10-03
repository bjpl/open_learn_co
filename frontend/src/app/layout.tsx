'use client'

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { ErrorBoundary } from '@/components/error-boundary'
import { reportWebVitals, initPerformanceMonitoring } from '@/lib/performance'
import { useEffect } from 'react'
import dynamic from 'next/dynamic'

// Lazy load Navbar for better initial bundle size
const Navbar = dynamic(() => import('@/components/Navbar'), {
  ssr: true,
  loading: () => (
    <div className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 animate-pulse"></div>
  ),
})

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  preload: true,
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'OpenLearn Colombia - Open Data Intelligence',
  description: 'Real-time Colombian open data aggregation and intelligence platform',
  keywords: ['Colombia', 'Open Data', 'Intelligence', 'News', 'Analytics'],
  authors: [{ name: 'OpenLearn Colombia' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#ffffff',
  robots: 'index, follow',
  openGraph: {
    type: 'website',
    locale: 'es_CO',
    url: 'https://openlearn-colombia.com',
    title: 'OpenLearn Colombia - Open Data Intelligence',
    description: 'Real-time Colombian open data aggregation and intelligence platform',
    siteName: 'OpenLearn Colombia',
  },
}

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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" suppressHydrationWarning className={inter.variable}>
      <head>
        <link rel="dns-prefetch" href="//localhost:8000" />
        <link rel="preconnect" href="http://localhost:8000" />
      </head>
      <body className={inter.className}>
        <ErrorBoundary
          onError={(error, errorInfo) => {
            console.error('[RootLayout] Application error:', {
              error: error.message,
              stack: error.stack,
              componentStack: errorInfo.componentStack,
            })
          }}
        >
          <Providers>
            <PerformanceMonitor />
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
              <Navbar />
              <main className="container mx-auto px-4 py-8">
                {children}
              </main>
            </div>
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  )
}