/**
 * Structured logging utility for OpenLearn Colombia
 *
 * Provides environment-aware logging with proper production behavior.
 * In development: Logs to console for debugging
 * In production: Only logs errors (to Sentry if configured)
 */

const isDev = process.env.NODE_ENV === 'development'

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogEntry {
  level: LogLevel
  message: string
  data?: any
  timestamp: string
}

class Logger {
  private log(level: LogLevel, message: string, ...args: any[]) {
    const entry: LogEntry = {
      level,
      message,
      data: args.length > 0 ? args : undefined,
      timestamp: new Date().toISOString()
    }

    // In development, log everything to console
    if (isDev) {
      const prefix = `[${entry.level.toUpperCase()}] ${entry.timestamp}`
      switch (level) {
        case 'debug':
          console.log(prefix, message, ...args)
          break
        case 'info':
          console.info(prefix, message, ...args)
          break
        case 'warn':
          console.warn(prefix, message, ...args)
          break
        case 'error':
          console.error(prefix, message, ...args)
          break
      }
    }

    // In production, only log errors
    if (!isDev && level === 'error') {
      console.error(`[ERROR] ${message}`, ...args)

      // Send to Sentry if available
      if (typeof window !== 'undefined' && (window as any).Sentry) {
        const error = args[0] instanceof Error ? args[0] : new Error(message)
        ;(window as any).Sentry.captureException(error, {
          extra: { data: entry.data }
        })
      }
    }

    // Could also send to analytics/monitoring service here
    // e.g., window.gtag?.('event', 'log', { level, message })
  }

  /**
   * Debug-level logs (only in development)
   * Use for detailed debugging information
   */
  debug(message: string, ...args: any[]) {
    this.log('debug', message, ...args)
  }

  /**
   * Info-level logs (only in development)
   * Use for general informational messages
   */
  info(message: string, ...args: any[]) {
    this.log('info', message, ...args)
  }

  /**
   * Warning-level logs (only in development)
   * Use for warning messages that aren't errors
   */
  warn(message: string, ...args: any[]) {
    this.log('warn', message, ...args)
  }

  /**
   * Error-level logs (always logged, even in production)
   * Use for error conditions that should be tracked
   */
  error(message: string, ...args: any[]) {
    this.log('error', message, ...args)
  }
}

// Export singleton instance
export const logger = new Logger()

// Export for backwards compatibility with console API
export default logger
