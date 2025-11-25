import { render, screen, act } from '@/test-utils'
import Toast from '@/components/Toast'

describe('Toast Component', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders success toast', () => {
    render(
      <Toast
        message="Operation successful"
        type="success"
        onClose={jest.fn()}
      />
    )

    expect(screen.getByText('Operation successful')).toBeInTheDocument()
  })

  it('renders error toast', () => {
    render(
      <Toast
        message="An error occurred"
        type="error"
        onClose={jest.fn()}
      />
    )

    expect(screen.getByText('An error occurred')).toBeInTheDocument()
  })

  it('renders info toast', () => {
    render(
      <Toast
        message="Information message"
        type="info"
        onClose={jest.fn()}
      />
    )

    expect(screen.getByText('Information message')).toBeInTheDocument()
  })

  it('calls onClose when close button clicked', () => {
    const onClose = jest.fn()

    render(
      <Toast
        message="Test message"
        type="success"
        onClose={onClose}
      />
    )

    const closeButton = screen.getByRole('button')
    closeButton.click()

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('auto-dismisses after timeout', () => {
    const onClose = jest.fn()

    render(
      <Toast
        message="Test message"
        type="success"
        onClose={onClose}
        duration={3000}
      />
    )

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(3000)
    })

    expect(onClose).toHaveBeenCalled()
  })
})
