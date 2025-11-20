/**
 * Authentication Hook
 * Provides authentication state and user information across the app
 */

'use client'

import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { logger } from '@/utils/logger'

export interface User {
  id: number
  email: string
  full_name: string
  username?: string
  is_active: boolean
  created_at: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isAuthenticated = !!user

  // Check if user is authenticated on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        // Try to get user info - cookie will be sent automatically
        // If no cookie exists, server will return 401
        const response = await fetch('/api/v1/auth/me', {
          credentials: 'include'  // Send cookies (including access_token)
        })

        if (response.ok) {
          const userData = await response.json()
          setUser(userData)
        }
        // If 401, user is not authenticated (no valid cookie)
        // This is normal - user just needs to log in
      } catch (err) {
        logger.error('Failed to load user', err)
        setError('Failed to load user session')
      } finally {
        setIsLoading(false)
      }
    }

    loadUser()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const formData = new FormData()
      formData.append('username', email) // OAuth2 spec uses 'username' field
      formData.append('password', password)

      const response = await fetch('/api/v1/auth/token', {
        method: 'POST',
        credentials: 'include',  // CRITICAL: Send cookies with request
        body: formData
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Login failed')
      }

      const data = await response.json()

      // SECURITY: Tokens are now in httpOnly cookies (not accessible via JS)
      // No localStorage storage needed - prevents XSS attacks!
      // Cookies are automatically sent with subsequent requests

      // Set user from response
      setUser(data.user)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      // Call logout endpoint to invalidate refresh token and clear cookies
      // Cookies are automatically sent with the request (credentials: 'include')
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include'  // Send cookies (including access_token)
      })
    } catch (err) {
      logger.error('Logout error', err)
    } finally {
      // Clear local state
      // No localStorage to clear - tokens are in httpOnly cookies
      // Server clears cookies automatically
      setUser(null)
      setError(null)
    }
  }

  const refreshUser = async () => {
    try {
      // Cookies are automatically sent with the request
      const response = await fetch('/api/v1/auth/me', {
        credentials: 'include'  // Send cookies (including access_token)
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      }
    } catch (err) {
      logger.error('Failed to refresh user', err)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        error,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

/**
 * Hook to get current user ID (for compatibility with existing code)
 */
export function useUserId(): string | null {
  const { user } = useAuth()
  return user ? user.id.toString() : null
}

/**
 * Hook to get current user information
 */
export function useCurrentUser(): User | null {
  const { user } = useAuth()
  return user
}

/**
 * Hook to check if user is authenticated
 */
export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth()
  return isAuthenticated
}
