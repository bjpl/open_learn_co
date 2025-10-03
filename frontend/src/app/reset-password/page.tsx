/**
 * Reset Password Page
 * Password reset confirmation with token
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { PasswordResetForm } from '@/components/auth/PasswordResetForm';
import { CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [token, setToken] = useState<string>('');
  const [resetComplete, setResetComplete] = useState(false);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setMessage({
        type: 'error',
        text: 'Invalid or missing reset token. Please request a new password reset.',
      });
    }
  }, [searchParams]);

  const handleSuccess = () => {
    setResetComplete(true);
    setMessage({
      type: 'success',
      text: 'Password reset successful! You can now login with your new password.',
    });
  };

  const handleError = (error: string) => {
    setMessage({ type: 'error', text: error });
  };

  if (!token && !message) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {resetComplete ? 'Password reset complete' : 'Set new password'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {resetComplete
              ? 'Your password has been successfully reset'
              : 'Choose a strong password for your account'}
          </p>
        </div>

        {/* Alert Messages */}
        {message && (
          <div
            className={`rounded-lg p-4 ${
              message.type === 'success'
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <div className="flex items-center gap-2">
              {message.type === 'success' ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" />
              )}
              <p
                className={`text-sm ${
                  message.type === 'success' ? 'text-green-800' : 'text-red-800'
                }`}
              >
                {message.text}
              </p>
            </div>
          </div>
        )}

        {/* Password Reset Form or Success Message */}
        <div className="bg-white py-8 px-6 shadow rounded-lg">
          {resetComplete ? (
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <CheckCircle2 className="h-16 w-16 text-green-600" />
              </div>
              <p className="text-sm text-gray-600">
                Your password has been successfully reset. You can now login with your new
                password.
              </p>
              <div className="pt-4">
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center w-full px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Continue to login
                </Link>
              </div>
            </div>
          ) : token ? (
            <>
              <PasswordResetForm
                mode="confirm"
                token={token}
                onSuccess={handleSuccess}
                onError={handleError}
              />

              {/* Back to Login */}
              <div className="mt-6">
                <Link
                  href="/login"
                  className="flex items-center justify-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to login
                </Link>
              </div>
            </>
          ) : (
            <div className="text-center space-y-4">
              <p className="text-sm text-gray-600">
                The reset link is invalid or has expired. Please request a new password reset.
              </p>
              <div className="pt-4">
                <Link
                  href="/forgot-password"
                  className="inline-flex items-center justify-center w-full px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Request new reset link
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
