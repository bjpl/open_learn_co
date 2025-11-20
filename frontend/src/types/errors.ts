/**
 * Custom Error Types for OpenLearn Platform
 * Provides typed error handling across the application
 */

import { logger } from '@/utils/logger'

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public endpoint?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
    Object.setPrototypeOf(this, APIError.prototype);
  }
}

export class NetworkError extends Error {
  constructor(
    message: string = 'Network connection failed',
    public originalError?: Error
  ) {
    super(message);
    this.name = 'NetworkError';
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public field?: string,
    public validationErrors?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export class AuthenticationError extends Error {
  constructor(
    message: string = 'Authentication required',
    public redirectUrl?: string
  ) {
    super(message);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

export class NotFoundError extends Error {
  constructor(
    message: string = 'Resource not found',
    public resourceType?: string,
    public resourceId?: string | number
  ) {
    super(message);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

export class PermissionError extends Error {
  constructor(
    message: string = 'Permission denied',
    public requiredPermission?: string
  ) {
    super(message);
    this.name = 'PermissionError';
    Object.setPrototypeOf(this, PermissionError.prototype);
  }
}

export type AppError =
  | APIError
  | NetworkError
  | ValidationError
  | AuthenticationError
  | NotFoundError
  | PermissionError
  | Error;

/**
 * Error reporting service integration point
 */
export interface ErrorReporter {
  report(error: Error, context?: Record<string, unknown>): void;
  setUser?(userId: string, userInfo?: Record<string, unknown>): void;
}

/**
 * Default console-based error reporter for development
 */
export class ConsoleErrorReporter implements ErrorReporter {
  report(error: Error, context?: Record<string, unknown>): void {
    logger.error('[Error Reporter]', {
      name: error.name,
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
    });
  }

  setUser(userId: string, userInfo?: Record<string, unknown>): void {
    logger.info('[Error Reporter] User set:', { userId, ...userInfo });
  }
}

// Global error reporter instance (can be replaced with Sentry, etc.)
export let errorReporter: ErrorReporter = new ConsoleErrorReporter();

export function setErrorReporter(reporter: ErrorReporter): void {
  errorReporter = reporter;
}
