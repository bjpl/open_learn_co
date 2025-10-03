'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Database, Newspaper, TrendingUp, BarChart3, Globe, User, LogOut, LogIn, Settings } from 'lucide-react'
import { useAuth } from '@/lib/auth/use-auth'
import { LogoutButton } from './auth/LogoutButton'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'News Feed', href: '/news', icon: Newspaper },
  { name: 'Data Sources', href: '/sources', icon: Database },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Trends', href: '/trends', icon: TrendingUp },
]

export default function Navbar() {
  const pathname = usePathname()
  const { isAuthenticated, user, isLoading } = useAuth()

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

            {/* Authentication Status */}
            <div className="flex items-center space-x-3 border-l border-gray-200 dark:border-gray-700 pl-4">
              {isLoading ? (
                <div className="h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse"></div>
              ) : isAuthenticated && user ? (
                <>
                  {/* User Menu */}
                  <Link
                    href="/profile"
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <User className="w-4 h-4" />
                    <span className="hidden lg:inline">{user.full_name || user.email}</span>
                  </Link>

                  {/* Preferences Link */}
                  <Link
                    href="/preferences"
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    title="User Preferences"
                  >
                    <Settings className="w-4 h-4" />
                    <span className="hidden lg:inline">Settings</span>
                  </Link>

                  {/* Logout Button */}
                  <LogoutButton
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    showIcon={true}
                  >
                    <span className="hidden lg:inline">Logout</span>
                  </LogoutButton>
                </>
              ) : (
                <>
                  {/* Login Button */}
                  <Link
                    href="/login"
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <LogIn className="w-4 h-4" />
                    <span className="hidden lg:inline">Login</span>
                  </Link>

                  {/* Register Button */}
                  <Link
                    href="/register"
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                  >
                    <span>Sign Up</span>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}