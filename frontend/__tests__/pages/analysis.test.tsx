import { render, screen, waitFor } from '@/test-utils'
import { clearAllMocks } from '@/test-utils'
import { mockCompletedAnalysis } from '@/test-utils/mockData'
import Analysis from '@/pages/analysis'

// Mock next/router with events and query params
const mockPush = jest.fn()
const mockReplace = jest.fn()
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/analysis',
    push: mockPush,
    replace: mockReplace,
    query: { job_id: 'job_001' },
    isReady: true,
    events: {
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn(),
    },
  }),
}))

// Mock config
jest.mock('@/lib/config', () => ({
  API_URL: 'http://localhost:8000',
}))

describe('Analysis Page', () => {
  beforeEach(() => {
    clearAllMocks()
    mockPush.mockClear()
    mockReplace.mockClear()
  })

  it('displays loading state initially', () => {
    global.fetch = jest.fn(() => new Promise(() => {})) as jest.Mock

    render(<Analysis />)

    // Should show loading skeleton (animate-pulse)
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('displays completed analysis results', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockCompletedAnalysis,
    }) as jest.Mock

    render(<Analysis />)

    await waitFor(() => {
      expect(screen.getByText(/Portfolio Analysis Results/i)).toBeInTheDocument()
    })
  })

  it('displays failed analysis state', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...mockCompletedAnalysis,
        status: 'failed',
        error_message: 'Analysis failed due to timeout',
      }),
    }) as jest.Mock

    render(<Analysis />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Analysis Failed/i })).toBeInTheDocument()
    })
  })

  it('displays in-progress state', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 'job_001',
        status: 'running',
        created_at: '2025-01-15T10:00:00Z',
        job_type: 'portfolio_analysis',
      }),
    }) as jest.Mock

    render(<Analysis />)

    await waitFor(() => {
      expect(screen.getByText(/Analysis In Progress/i)).toBeInTheDocument()
    })
  })
})
