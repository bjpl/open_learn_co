/**
 * Error Fallback UI Component
 * User-friendly error display with recovery options
 */

import React from 'react';
import Link from 'next/link';
import { AlertTriangle, Home, RefreshCw, Mail } from 'lucide-react';

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
  showDetails?: boolean;
}

export function ErrorFallback({ error, resetError, showDetails = false }: ErrorFallbackProps) {
  const isDevelopment = process.env.NODE_ENV === 'development';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        <div className="flex items-center justify-center mb-6">
          <div className="bg-red-100 rounded-full p-4">
            <AlertTriangle className="h-12 w-12 text-red-600" />
          </div>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 text-center mb-4">
          Oops! Something went wrong
        </h1>

        <p className="text-gray-600 text-center mb-8">
          We're sorry for the inconvenience. An unexpected error occurred while processing your request.
        </p>

        {/* Error Details (Development Mode or if showDetails=true) */}
        {(isDevelopment || showDetails) && (
          <div className="mb-8 bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Error Details:</h2>
            <p className="text-sm text-red-600 font-mono mb-2">{error.name}: {error.message}</p>
            {error.stack && (
              <details className="mt-2">
                <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-900">
                  Stack Trace
                </summary>
                <pre className="mt-2 text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap">
                  {error.stack}
                </pre>
              </details>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={resetError}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-5 w-5" />
            Try Again
          </button>

          <Link
            href="/"
            className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Home className="h-5 w-5" />
            Go Home
          </Link>

          <a
            href="mailto:support@openlearn.example.com?subject=Error Report"
            className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Mail className="h-5 w-5" />
            Contact Support
          </a>
        </div>

        {/* Additional Help */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">What can you do?</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Try refreshing the page or clicking "Try Again" above</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Return to the homepage and try a different action</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Contact our support team if the problem persists</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Check your internet connection</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

/**
 * Compact Error Fallback for smaller components
 */
interface CompactErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

export function CompactErrorFallback({ error, resetError }: CompactErrorFallbackProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-red-900 mb-1">
            Error loading component
          </h3>
          <p className="text-sm text-red-700 mb-3">
            {error.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={resetError}
            className="text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    </div>
  );
}
