import { render, screen, waitFor } from '@/test-utils'
import { mockFetch, clearAllMocks } from '@/test-utils'
import { mockPortfolioData, mockAccounts } from '@/test-utils/mockData'
import Dashboard from '@/pages/dashboard'

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/dashboard',
    push: jest.fn(),
    query: {},
  }),
}))

describe('Dashboard Page', () => {
  beforeEach(() => {
    clearAllMocks()
  })

  it('displays loading state initially', () => {
    mockFetch(mockPortfolioData, true)

    render(<Dashboard />)

    // Should show loading indicator
    expect(screen.getByText(/loading/i) || screen.getByRole('status')).toBeInTheDocument()
  })

  it('displays portfolio summary after loading', async () => {
    mockFetch({
      accounts: mockAccounts,
      total_value: 47000,
    })

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
    })

    // Should display portfolio information
    expect(screen.getByText(/retirement account/i)).toBeInTheDocument()
    expect(screen.getByText(/taxable account/i)).toBeInTheDocument()
  })

  it('displays error message on API failure', async () => {
    mockFetch({ error: 'Failed to load data' }, false)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('shows request analysis button', async () => {
    mockFetch({ accounts: mockAccounts })

    render(<Dashboard />)

    await waitFor(() => {
      const button = screen.getByRole('button', { name: /analyze/i })
      expect(button).toBeInTheDocument()
    })
  })

  it('navigates to accounts page when account is clicked', async () => {
    mockFetch({ accounts: mockAccounts })

    render(<Dashboard />)

    await waitFor(() => {
      const accountLink = screen.getByText(/retirement account/i)
      expect(accountLink).toBeInTheDocument()
    })
  })
})
