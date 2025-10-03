/**
 * Auth Guard Component
 * Wrapper component for protecting routes that require authentication
 */

'use client';

import React from 'react';
import { ProtectedRoute } from '@/lib/auth/protected-route';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  redirectTo?: string;
  fallback?: React.ReactNode;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requireAuth = true,
  redirectTo = '/login',
  fallback,
}) => {
  return (
    <ProtectedRoute requireAuth={requireAuth} redirectTo={redirectTo}>
      {children}
    </ProtectedRoute>
  );
};
