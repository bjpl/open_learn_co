'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Database, Newspaper, TrendingUp, BarChart3, Globe, User, LogOut, LogIn, Settings, Menu, X } from 'lucide-react'
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const mobileMenuRef = useRef<HTMLDivElement>(null)

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [pathname])

  // Handle Escape key to close mobile menu
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileMenuOpen) {
        setIsMobileMenuOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isMobileMenuOpen])

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isMobileMenuOpen])

  // Handle click outside to close mobile menu
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(e.target as Node)) {
        setIsMobileMenuOpen(false)
      }
    }

    if (isMobileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isMobileMenuOpen])

  return (
    <nav aria-label="Main navigation" className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" aria-label="OpenLearn Colombia home" className="flex items-center space-x-3">
              <Globe className="w-8 h-8 text-yellow-500" aria-hidden="true" />
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

          {/* Desktop Navigation - Hidden on Mobile */}
          <div className="hidden md:block">
            <nav aria-label="Primary navigation" className="ml-10 flex items-baseline space-x-4">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    aria-label={item.name}
                    aria-current={isActive ? 'page' : undefined}
                    className={`
                      flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors
                      ${isActive
                        ? 'bg-yellow-500 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4 mr-2" aria-hidden="true" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            {/* Mobile Menu Button - Visible only on Mobile */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-yellow-500"
              aria-label={isMobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-menu"
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" aria-hidden="true" />
              ) : (
                <Menu className="w-6 h-6" aria-hidden="true" />
              )}
            </button>
            <div className="flex items-center space-x-2 text-sm" role="status" aria-live="polite">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" aria-hidden="true"></div>
              <span className="text-gray-600 dark:text-gray-400">Live</span>
              <span className="sr-only">System is online and operational</span>
            </div>

            {/* Authentication Status */}
            <nav aria-label="User menu" className="flex items-center space-x-3 border-l border-gray-200 dark:border-gray-700 pl-4">
              {isLoading ? (
                <div className="h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" aria-label="Loading user information"></div>
              ) : isAuthenticated && user ? (
                <>
                  {/* User Menu */}
                  <Link
                    href="/profile"
                    aria-label={`View profile for ${user.full_name || user.email}`}
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <User className="w-4 h-4" aria-hidden="true" />
                    <span className="hidden lg:inline">{user.full_name || user.email}</span>
                  </Link>

                  {/* Preferences Link */}
                  <Link
                    href="/preferences"
                    aria-label="User preferences and settings"
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Settings className="w-4 h-4" aria-hidden="true" />
                    <span className="hidden lg:inline">Settings</span>
                  </Link>

                  {/* Logout Button */}
                  <LogoutButton
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    showIcon={true}
                    aria-label="Log out of your account"
                  >
                    <span className="hidden lg:inline">Logout</span>
                  </LogoutButton>
                </>
              ) : (
                <>
                  {/* Login Button */}
                  <Link
                    href="/login"
                    aria-label="Sign in to your account"
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <LogIn className="w-4 h-4" aria-hidden="true" />
                    <span className="hidden lg:inline">Login</span>
                  </Link>

                  {/* Register Button */}
                  <Link
                    href="/register"
                    aria-label="Create a new account"
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                  >
                    <span>Sign Up</span>
                  </Link>
                </>
              )}
            </nav>
          </div>
        </div>

        {/* Mobile Menu Backdrop - Visible only when menu is open */}
        {isMobileMenuOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
            aria-hidden="true"
          />
        )}

        {/* Mobile Menu Drawer - Slide-out from right */}
        <div
          ref={mobileMenuRef}
          id="mobile-menu"
          className={`
            fixed top-0 right-0 h-full w-64 bg-white dark:bg-gray-800 shadow-xl z-50
            transform transition-transform duration-300 ease-in-out md:hidden
            ${isMobileMenuOpen ? 'translate-x-0' : 'translate-x-full'}
          `}
          role="dialog"
          aria-label="Mobile navigation menu"
          aria-modal="true"
        >
          {/* Mobile Menu Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <span className="text-lg font-semibold text-gray-900 dark:text-white">Menu</span>
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-yellow-500"
              aria-label="Close menu"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Mobile Navigation Links */}
          <nav className="p-4 space-y-2" aria-label="Mobile navigation">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  aria-label={item.name}
                  aria-current={isActive ? 'page' : undefined}
                  className={`
                    flex items-center px-4 py-3 rounded-md text-base font-medium transition-colors
                    min-h-[44px] min-w-[44px]
                    ${isActive
                      ? 'bg-yellow-500 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }
                  `}
                  onClick={() => setIsMobileMenuOpen(false)}
                  tabIndex={0}
                >
                  <Icon className="w-5 h-5 mr-3" aria-hidden="true" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* Mobile Auth Section */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            {isLoading ? (
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded-md animate-pulse" aria-label="Loading user information"></div>
            ) : isAuthenticated && user ? (
              <div className="space-y-2">
                <Link
                  href="/profile"
                  aria-label={`View profile for ${user.full_name || user.email}`}
                  className="flex items-center px-4 py-3 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors min-h-[44px]"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <User className="w-5 h-5 mr-3" aria-hidden="true" />
                  {user.full_name || user.email}
                </Link>
                <Link
                  href="/preferences"
                  aria-label="User preferences and settings"
                  className="flex items-center px-4 py-3 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors min-h-[44px]"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <Settings className="w-5 h-5 mr-3" aria-hidden="true" />
                  Settings
                </Link>
                <LogoutButton
                  className="w-full flex items-center px-4 py-3 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors min-h-[44px]"
                  showIcon={true}
                  aria-label="Log out of your account"
                >
                  Logout
                </LogoutButton>
              </div>
            ) : (
              <div className="space-y-2">
                <Link
                  href="/login"
                  aria-label="Sign in to your account"
                  className="flex items-center justify-center px-4 py-3 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors min-h-[44px]"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <LogIn className="w-5 h-5 mr-2" aria-hidden="true" />
                  Login
                </Link>
                <Link
                  href="/register"
                  aria-label="Create a new account"
                  className="flex items-center justify-center px-4 py-3 rounded-md text-base font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors min-h-[44px]"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}