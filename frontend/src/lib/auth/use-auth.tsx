/**
 * Authentication Hook (Extended with Password Reset)
 * Re-exports useAuth from hooks directory and adds password reset functions
 */

'use client'

import { useAuth as useBaseAuth } from '@/hooks/useAuth'
import type { PasswordResetRequestData, PasswordResetConfirmData } from '../validations/auth-schemas'

// Re-export base auth types and provider
export { AuthProvider, useUserId, useCurrentUser, useIsAuthenticated } from '@/hooks/useAuth'
export type { User, AuthState } from '@/hooks/useAuth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Extended auth hook with password reset functionality
 */
export function useAuth() {
  const baseAuth = useBaseAuth()

  /**
   * Request password reset email
   */
  const requestPasswordReset = async (email: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/password-reset`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({ detail: 'Failed to send reset email' }))
      throw new Error(data.detail || 'Failed to send reset email')
    }

    return
  }

  /**
   * Reset password with token
   */
  const resetPassword = async (data: PasswordResetConfirmData): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/password-update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: data.token,
        new_password: data.new_password,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to reset password' }))
      throw new Error(errorData.detail || 'Failed to reset password')
    }

    return
  }

  return {
    ...baseAuth,
    requestPasswordReset,
    resetPassword,
  }
}
