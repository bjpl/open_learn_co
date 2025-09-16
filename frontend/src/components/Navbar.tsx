'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Database, Newspaper, TrendingUp, BarChart3, Globe } from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'News Feed', href: '/news', icon: Newspaper },
  { name: 'Data Sources', href: '/sources', icon: Database },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Trends', href: '/trends', icon: TrendingUp },
]

export default function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-3">
              <Globe className="w-8 h-8 text-yellow-500" />
              <div>
                <span className="text-xl font-bold text-gray-900 dark:text-white">
                  OpenLearn Colombia
                </span>
                <span className="block text-xs text-gray-500 dark:text-gray-400">
                  Data Intelligence Platform
                </span>
              </div>
            </Link>
          </div>
          
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`
                      flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors
                      ${isActive
                        ? 'bg-yellow-500 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-gray-600 dark:text-gray-400">Live</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}