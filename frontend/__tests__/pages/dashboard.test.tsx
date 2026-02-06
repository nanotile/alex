import { render, screen, waitFor } from '@/test-utils'
import { clearAllMocks } from '@/test-utils'
import Dashboard from '@/pages/dashboard'

// Mock next/router with events (needed by Layout > PageTransition)
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/dashboard',
    push: jest.fn(),
    query: {},
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

describe('Dashboard Page', () => {
  beforeEach(() => {
    clearAllMocks()
  })

  it('displays loading state initially', () => {
    // Mock fetch to never resolve (keeps loading state)
    global.fetch = jest.fn(() => new Promise(() => {})) as jest.Mock

    render(<Dashboard />)

    // Dashboard shows skeleton loading state
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('displays dashboard heading after loading', async () => {
    // Mock the user API response
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: {
            clerk_user_id: 'test_user_001',
            display_name: 'Test User',
            years_until_retirement: 20,
            target_retirement_income: 80000,
            asset_class_targets: { equity: 70, fixed_income: 30 },
            region_targets: { north_america: 60, international: 40 },
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([]),  // empty accounts
      }) as jest.Mock

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    })
  })

  it('displays error when API fails', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
    }) as jest.Mock

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText(/failed to sync user/i)).toBeInTheDocument()
    })
  })
})
