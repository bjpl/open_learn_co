/**
 * React Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 */

'use client';

import React, { Component, ReactNode } from 'react';
import { ErrorFallback, CompactErrorFallback } from './error-fallback';
import { errorReporter } from '@/types/errors';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, resetError: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  compact?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Main Error Boundary Class Component
 * Note: Error boundaries must be class components in React
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log error to error reporting service
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);

    // Report to external service (Sentry, etc.)
    errorReporter.report(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: 'ErrorBoundary',
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Update state with error info
    this.setState({
      errorInfo,
    });
  }

  resetError = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetError);
      }

      // Use compact fallback
      if (this.props.compact) {
        return <CompactErrorFallback error={this.state.error} resetError={this.resetError} />;
      }

      // Default full-page fallback
      return <ErrorFallback error={this.state.error} resetError={this.resetError} />;
    }

    return this.props.children;
  }
}

/**
 * Hook for functional component error handling
 * Note: This doesn't catch render errors, only async errors
 */
export function useErrorHandler(): (error: Error) => void {
  return React.useCallback((error: Error) => {
    console.error('[useErrorHandler] Error thrown:', error);
    errorReporter.report(error, {
      handler: 'useErrorHandler',
    });
    throw error; // Re-throw to be caught by Error Boundary
  }, []);
}

/**
 * HOC to wrap components with error boundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
): React.FC<P> {
  const WrappedComponent: React.FC<P> = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name || 'Component'})`;

  return WrappedComponent;
}

/**
 * Route-level error boundary with custom styling
 */
export function RouteErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('[RouteErrorBoundary] Route error:', {
          error: error.message,
          stack: error.stack,
          componentStack: errorInfo.componentStack,
        });
      }}
    >
      {children}
    </ErrorBoundary>
  );
}

/**
 * Component-level error boundary (compact)
 */
export function ComponentErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary compact onError={(error) => {
      console.warn('[ComponentErrorBoundary] Component error:', error.message);
    }}>
      {children}
    </ErrorBoundary>
  );
}
