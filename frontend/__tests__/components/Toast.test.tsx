import { render, screen, act } from '@testing-library/react'
import { ToastContainer, showToast } from '@/components/Toast'

describe('Toast Component', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders success toast', () => {
    render(<ToastContainer />)

    act(() => {
      showToast('success', 'Operation successful')
    })

    expect(screen.getByText('Operation successful')).toBeInTheDocument()
  })

  it('renders error toast', () => {
    render(<ToastContainer />)

    act(() => {
      showToast('error', 'An error occurred')
    })

    expect(screen.getByText('An error occurred')).toBeInTheDocument()
  })

  it('renders info toast', () => {
    render(<ToastContainer />)

    act(() => {
      showToast('info', 'Information message')
    })

    expect(screen.getByText('Information message')).toBeInTheDocument()
  })

  it('calls onClose when close button clicked', () => {
    render(<ToastContainer />)

    act(() => {
      showToast('success', 'Test message')
    })

    const closeButton = screen.getByRole('button')
    act(() => {
      closeButton.click()
    })

    expect(screen.queryByText('Test message')).not.toBeInTheDocument()
  })

  it('auto-dismisses after timeout', () => {
    render(<ToastContainer />)

    act(() => {
      showToast('success', 'Test message', 3000)
    })

    expect(screen.getByText('Test message')).toBeInTheDocument()

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(3000)
    })

    expect(screen.queryByText('Test message')).not.toBeInTheDocument()
  })
})
