import { render, screen } from '@/test-utils'
import Layout from '@/components/Layout'

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/dashboard',
    push: jest.fn(),
    query: {},
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
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument()
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
