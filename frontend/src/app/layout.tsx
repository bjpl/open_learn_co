import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import ClientLayout from './ClientLayout'

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
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
