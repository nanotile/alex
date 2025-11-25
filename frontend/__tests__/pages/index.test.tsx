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

  it('displays welcome message', () => {
    render(<Home />)

    expect(screen.getByText(/welcome/i)).toBeInTheDocument()
  })

  it('shows call-to-action for authenticated users', () => {
    render(<Home />)

    // Should have a link to dashboard or get started button
    const cta = screen.getByRole('link', { name: /dashboard|get started/i })
    expect(cta).toBeInTheDocument()
  })

  it('displays key features', () => {
    render(<Home />)

    // Should highlight main features
    expect(screen.getByText(/portfolio/i)).toBeInTheDocument()
    expect(screen.getByText(/analysis|insights/i)).toBeInTheDocument()
  })
})
