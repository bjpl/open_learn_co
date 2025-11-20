/**
 * Registration Form Component
 * User registration with validation and password strength indicator
 */

'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { registerSchema, RegisterFormData, getPasswordStrength } from '@/lib/validations/auth-schemas';
import { useAuth } from '@/lib/auth/use-auth';

interface RegisterFormProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, onError }) => {
  const { register: registerUser, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordValue, setPasswordValue] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirm_password: '',
      full_name: '',
      terms_accepted: false,
    },
  });

  const password = watch('password');
  const passwordStrength = password ? getPasswordStrength(password) : null;

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data);
      onSuccess?.();
    } catch (error: any) {
      onError?.(error.message || 'Registration failed');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" aria-label="Registration form">
      {/* Full Name Field */}
      <div>
        <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
          Full Name (Optional)
        </label>
        <input
          {...register('full_name')}
          id="full_name"
          type="text"
          autoComplete="name"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="John Doe"
          disabled={isLoading}
          aria-required="false"
          aria-invalid={!!errors.full_name}
          aria-describedby={errors.full_name ? 'full-name-error' : undefined}
        />
        {errors.full_name && (
          <p id="full-name-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.full_name.message}
          </p>
        )}
      </div>

      {/* Email Field */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
          Email Address <span className="text-red-600" aria-hidden="true">*</span>
        </label>
        <input
          {...register('email')}
          id="email"
          type="email"
          autoComplete="email"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="you@example.com"
          disabled={isLoading}
          aria-required="true"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {errors.email && (
          <p id="email-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.email.message}
          </p>
        )}
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
          Password <span className="text-red-600" aria-hidden="true">*</span>
        </label>
        <div className="relative">
          <input
            {...register('password', {
              onChange: (e) => setPasswordValue(e.target.value),
            })}
            id="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
            placeholder="Create a strong password"
            disabled={isLoading}
            aria-required="true"
            aria-invalid={!!errors.password}
            aria-describedby={passwordStrength ? 'password-strength password-error' : errors.password ? 'password-error' : undefined}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={20} aria-hidden="true" /> : <Eye size={20} aria-hidden="true" />}
          </button>
        </div>

        {/* Password Strength Indicator */}
        {passwordStrength && (
          <div id="password-strength" className="mt-2" role="status" aria-live="polite">
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
            <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={passwordStrength.score} aria-valuemin={0} aria-valuemax={7} aria-label={`Password strength: ${passwordStrength.label}`}>
              <div
                className={`h-2 rounded-full transition-all ${passwordStrength.color}`}
                style={{ width: `${(passwordStrength.score / 7) * 100}%` }}
                aria-hidden="true"
              />
            </div>
          </div>
        )}

        {errors.password && (
          <p id="password-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.password.message}
          </p>
        )}
      </div>

      {/* Confirm Password Field */}
      <div>
        <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-2">
          Confirm Password <span className="text-red-600" aria-hidden="true">*</span>
        </label>
        <div className="relative">
          <input
            {...register('confirm_password')}
            id="confirm_password"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
            placeholder="Confirm your password"
            disabled={isLoading}
            aria-required="true"
            aria-invalid={!!errors.confirm_password}
            aria-describedby={errors.confirm_password ? 'confirm-password-error' : undefined}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            tabIndex={-1}
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
          >
            {showConfirmPassword ? <EyeOff size={20} aria-hidden="true" /> : <Eye size={20} aria-hidden="true" />}
          </button>
        </div>
        {errors.confirm_password && (
          <p id="confirm-password-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.confirm_password.message}
          </p>
        )}
      </div>

      {/* Terms and Conditions */}
      <div>
        <div className="flex items-start">
          <input
            {...register('terms_accepted')}
            id="terms_accepted"
            type="checkbox"
            className="h-4 w-4 mt-1 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            disabled={isLoading}
            aria-required="true"
            aria-invalid={!!errors.terms_accepted}
            aria-describedby={errors.terms_accepted ? 'terms-error' : undefined}
          />
          <label htmlFor="terms_accepted" className="ml-2 block text-sm text-gray-700">
            I agree to the{' '}
            <a href="/terms" className="text-blue-600 hover:text-blue-500 font-medium">
              Terms and Conditions
            </a>{' '}
            and{' '}
            <a href="/privacy" className="text-blue-600 hover:text-blue-500 font-medium">
              Privacy Policy
            </a>
            <span className="text-red-600" aria-hidden="true"> *</span>
          </label>
        </div>
        {errors.terms_accepted && (
          <p id="terms-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.terms_accepted.message}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label={isLoading ? 'Creating account, please wait' : 'Create your account'}
      >
        {isLoading ? (
          <>
            <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" aria-hidden="true" />
            Creating account...
          </>
        ) : (
          'Create account'
        )}
      </button>
    </form>
  );
};
