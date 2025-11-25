import { render, screen, waitFor, fireEvent } from '@/test-utils'
import { mockFetch, clearAllMocks } from '@/test-utils'
import { mockAnalysisJob, mockCompletedAnalysis } from '@/test-utils/mockData'
import Analysis from '@/pages/analysis'

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/analysis',
    push: jest.fn(),
    query: {},
  }),
}))

describe('Analysis Page', () => {
  beforeEach(() => {
    clearAllMocks()
  })

  it('displays job history', async () => {
    mockFetch({
      jobs: [mockAnalysisJob],
    })

    render(<Analysis />)

    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
    })

    // Should display job in history
    expect(screen.getByText(/pending/i)).toBeInTheDocument()
  })

  it('shows request new analysis button', async () => {
    mockFetch({ jobs: [] })

    render(<Analysis />)

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /request.*analysis/i })
      expect(button).toBeInTheDocument()
    })
  })

  it('displays completed analysis results', async () => {
    mockFetch(mockCompletedAnalysis)

    render(<Analysis />)

    await waitFor(() => {
      // Should show report content
      expect(screen.getByText(/portfolio analysis report/i)).toBeInTheDocument()
    })

    // Should show charts
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
  })

  it('handles request analysis button click', async () => {
    mockFetch({ jobs: [] })
    const createJobMock = jest.fn().mockResolvedValue({ job_id: 'new_job' })
    global.fetch = createJobMock as any

    render(<Analysis />)

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /request.*analysis/i })
      fireEvent.click(button)
    })

    expect(createJobMock).toHaveBeenCalled()
  })

  it('polls for job status updates', async () => {
    // First return pending, then completed
    let callCount = 0
    global.fetch = jest.fn(() => {
      callCount++
      if (callCount === 1) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ...mockAnalysisJob, status: 'in_progress' }),
        })
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockCompletedAnalysis,
      })
    }) as jest.Mock

    render(<Analysis />)

    // Should eventually show completed status
    await waitFor(
      () => {
        expect(screen.getByText(/completed/i)).toBeInTheDocument()
      },
      { timeout: 5000 }
    )
  })

  it('displays error when analysis fails', async () => {
    mockFetch({
      ...mockAnalysisJob,
      status: 'failed',
      error_message: 'Analysis failed',
    })

    render(<Analysis />)

    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument()
    })
  })
})
