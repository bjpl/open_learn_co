/**
 * Forgot Password Page
 * Password reset request page
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { PasswordResetForm } from '@/components/auth/PasswordResetForm';
import { CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [emailSent, setEmailSent] = useState(false);

  const handleSuccess = () => {
    setEmailSent(true);
    setMessage({
      type: 'success',
      text: 'Password reset link sent! Check your email.',
    });
  };

  const handleError = (error: string) => {
    setMessage({ type: 'error', text: error });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Reset your password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {emailSent
              ? 'We sent you an email with instructions to reset your password'
              : 'Enter your email address and we will send you a reset link'}
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

        {/* Password Reset Form */}
        <div className="bg-white py-8 px-6 shadow rounded-lg">
          {!emailSent ? (
            <>
              <PasswordResetForm
                mode="request"
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
              <div className="flex justify-center">
                <CheckCircle2 className="h-16 w-16 text-green-600" />
              </div>
              <p className="text-sm text-gray-600">
                If an account exists with that email, you will receive password reset
                instructions shortly.
              </p>
              <div className="pt-4">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Return to login
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Help Text */}
        {!emailSent && (
          <div className="text-center">
            <p className="text-xs text-gray-500">
              Remember your password?{' '}
              <Link href="/login" className="text-blue-600 hover:text-blue-500">
                Sign in
              </Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
