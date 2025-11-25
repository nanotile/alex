import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { ClerkProvider } from '@clerk/nextjs'

/**
 * Custom render function that wraps components with necessary providers
 */
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return <ClerkProvider>{children}</ClerkProvider>
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything from React Testing Library
export * from '@testing-library/react'

// Override render method
export { customRender as render }

/**
 * Utility to wait for async operations
 */
export const waitForLoadingToFinish = () => {
  return new Promise((resolve) => {
    setTimeout(resolve, 0)
  })
}

/**
 * Mock fetch response helper
 */
export const mockFetch = (data: any, ok: boolean = true) => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok,
      json: async () => data,
      text: async () => JSON.stringify(data),
      status: ok ? 200 : 500,
    })
  ) as jest.Mock
}

/**
 * Clear all mocks helper
 */
export const clearAllMocks = () => {
  jest.clearAllMocks()
  if (global.fetch) {
    ;(global.fetch as jest.Mock).mockClear()
  }
}
