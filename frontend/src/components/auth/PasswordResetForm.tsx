/**
 * Password Reset Form Component
 * Handles both password reset request and confirmation
 */

'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Loader2, CheckCircle2 } from 'lucide-react';
import {
  passwordResetRequestSchema,
  passwordResetConfirmSchema,
  PasswordResetRequestData,
  PasswordResetConfirmData,
  getPasswordStrength,
} from '@/lib/validations/auth-schemas';
import { useAuth } from '@/lib/auth/use-auth';

interface PasswordResetFormProps {
  mode: 'request' | 'confirm';
  token?: string;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const PasswordResetForm: React.FC<PasswordResetFormProps> = ({
  mode,
  token = '',
  onSuccess,
  onError,
}) => {
  const { requestPasswordReset, resetPassword, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Request form
  const requestForm = useForm<PasswordResetRequestData>({
    resolver: zodResolver(passwordResetRequestSchema),
    defaultValues: { email: '' },
  });

  // Confirm form
  const confirmForm = useForm<PasswordResetConfirmData>({
    resolver: zodResolver(passwordResetConfirmSchema),
    defaultValues: {
      token,
      new_password: '',
      confirm_password: '',
    },
  });

  const password = confirmForm.watch('new_password');
  const passwordStrength = password ? getPasswordStrength(password) : null;

  const handleRequestSubmit = async (data: PasswordResetRequestData) => {
    try {
      await requestPasswordReset(data.email);
      onSuccess?.();
    } catch (error: any) {
      onError?.(error.message || 'Failed to send reset email');
    }
  };

  const handleConfirmSubmit = async (data: PasswordResetConfirmData) => {
    try {
      await resetPassword(data);
      onSuccess?.();
    } catch (error: any) {
      onError?.(error.message || 'Failed to reset password');
    }
  };

  if (mode === 'request') {
    return (
      <form onSubmit={requestForm.handleSubmit(handleRequestSubmit)} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
            Email Address
          </label>
          <input
            {...requestForm.register('email')}
            id="email"
            type="email"
            autoComplete="email"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="you@example.com"
            disabled={isLoading}
          />
          {requestForm.formState.errors.email && (
            <p className="mt-1 text-sm text-red-600">
              {requestForm.formState.errors.email.message}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
              Sending...
            </>
          ) : (
            'Send reset link'
          )}
        </button>
      </form>
    );
  }

  return (
    <form onSubmit={confirmForm.handleSubmit(handleConfirmSubmit)} className="space-y-6">
      {/* Hidden token field */}
      <input {...confirmForm.register('token')} type="hidden" />

      {/* New Password Field */}
      <div>
        <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-2">
          New Password
        </label>
        <div className="relative">
          <input
            {...confirmForm.register('new_password')}
            id="new_password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
            placeholder="Create a strong password"
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        </div>

        {/* Password Strength Indicator */}
        {passwordStrength && (
          <div className="mt-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600">Password strength:</span>
              <span className={`text-xs font-medium ${
                passwordStrength.score <= 2 ? 'text-red-600' :
                passwordStrength.score <= 4 ? 'text-yellow-600' :
                passwordStrength.score <= 5 ? 'text-blue-600' :
                'text-green-600'
              }`}>
                {passwordStrength.label}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${passwordStrength.color}`}
                style={{ width: `${(passwordStrength.score / 7) * 100}%` }}
              />
            </div>
          </div>
        )}

        {confirmForm.formState.errors.new_password && (
          <p className="mt-1 text-sm text-red-600">
            {confirmForm.formState.errors.new_password.message}
          </p>
        )}
      </div>

      {/* Confirm Password Field */}
      <div>
        <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-2">
          Confirm Password
        </label>
        <div className="relative">
          <input
            {...confirmForm.register('confirm_password')}
            id="confirm_password"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
            placeholder="Confirm your password"
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            tabIndex={-1}
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
          >
            {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        </div>
        {confirmForm.formState.errors.confirm_password && (
          <p className="mt-1 text-sm text-red-600">
            {confirmForm.formState.errors.confirm_password.message}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
            Resetting password...
          </>
        ) : (
          'Reset password'
        )}
      </button>
    </form>
  );
};
