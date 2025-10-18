/**
 * Test Utilities
 * OpenLearn Colombia - Custom render functions and test helpers
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PreferencesProvider } from '@/lib/preferences/preferences-context'
import { AuthProvider } from '@/lib/auth/auth-provider'

/**
 * Create a new QueryClient for testing
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0, // Phase 1: Updated from cacheTime (deprecated in React Query v5)
      },
      mutations: {
        retry: false,
      },
    },
  })
}

/**
 * All Providers Wrapper
 */
interface AllProvidersProps {
  children: React.ReactNode
  queryClient?: QueryClient
}

function AllProviders({ children, queryClient }: AllProvidersProps) {
  const client = queryClient || createTestQueryClient()

  return (
    <QueryClientProvider client={client}>
      <AuthProvider>
        <PreferencesProvider userId="test-user-123">
          {children}
        </PreferencesProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

/**
 * Custom render function with all providers
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient
}

export function renderWithProviders(
  ui: ReactElement,
  options?: CustomRenderOptions
): RenderResult {
  const { queryClient, ...renderOptions } = options || {}

  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders queryClient={queryClient}>{children}</AllProviders>
    ),
    ...renderOptions,
  })
}

/**
 * Create mock file for upload testing
 */
export function createMockFile(
  name: string = 'test.png',
  size: number = 1024,
  type: string = 'image/png'
): File {
  const blob = new Blob(['a'.repeat(size)], { type })
  return new File([blob], name, { type })
}

/**
 * Mock FileReader
 */
export class MockFileReader {
  onloadend: (() => void) | null = null
  result: string | ArrayBuffer | null = null

  readAsDataURL(file: File) {
    this.result = `data:${file.type};base64,mockbase64data`
    setTimeout(() => {
      if (this.onloadend) {
        this.onloadend()
      }
    }, 0)
  }
}

/**
 * Wait for element to be removed (async helper)
 */
export async function waitForElementToBeRemoved(
  callback: () => HTMLElement | null,
  options?: { timeout?: number }
) {
  const { timeout = 1000 } = options || {}
  const startTime = Date.now()

  while (callback() !== null) {
    if (Date.now() - startTime > timeout) {
      throw new Error('Timeout waiting for element to be removed')
    }
    await new Promise((resolve) => setTimeout(resolve, 50))
  }
}

/**
 * Mock API Response
 */
export function createMockApiResponse<T>(data: T, status: number = 200) {
  return {
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: {} as any,
  }
}

/**
 * Mock Error Response
 */
export function createMockErrorResponse(message: string, status: number = 500) {
  return {
    response: {
      data: { message },
      status,
      statusText: 'Error',
      headers: {},
      config: {} as any,
    },
  }
}

// Re-export everything from React Testing Library
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
