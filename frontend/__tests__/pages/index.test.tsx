import { render, screen } from '@/test-utils'
import Home from '@/pages/index'

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/',
    push: jest.fn(),
    query: {},
  }),
}))

describe('Home Page', () => {
  it('renders the main heading', () => {
    render(<Home />)

    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })

  it('displays hero section content', () => {
    render(<Home />)

    expect(screen.getByText(/AI-Powered Financial Future/i)).toBeInTheDocument()
  })

  it('shows dashboard link for authenticated users', () => {
    render(<Home />)

    // SignedIn mock renders children, so dashboard links should be visible
    const dashboardLinks = screen.getAllByText(/Go to Dashboard|Open Dashboard/i)
    expect(dashboardLinks.length).toBeGreaterThan(0)
  })

  it('displays key features', () => {
    render(<Home />)

    // Should highlight main features/agents
    expect(screen.getByText(/Portfolio Analyst/i)).toBeInTheDocument()
    expect(screen.getByText(/Chart Specialist/i)).toBeInTheDocument()
  })
})
