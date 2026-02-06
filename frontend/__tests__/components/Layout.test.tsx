import { render, screen } from '@/test-utils'
import Layout from '@/components/Layout'

// Mock next/router with events
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

describe('Layout Component', () => {
  it('renders navigation and children', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    expect(screen.getByText('Test Content')).toBeInTheDocument()
    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })

  it('renders main navigation links', () => {
    render(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    // Check for common navigation items
    expect(screen.getAllByText(/dashboard/i).length).toBeGreaterThan(0)
  })

  it('renders user button from Clerk', () => {
    render(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    expect(screen.getByTestId('user-button')).toBeInTheDocument()
  })

  it('applies correct structure', () => {
    const { container } = render(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    // Should have a main element
    const main = container.querySelector('main')
    expect(main).toBeInTheDocument()
  })
})
