import React from 'react'

// Mock Clerk components and hooks
export const ClerkProvider = ({ children }: { children: React.ReactNode }) => (
  <div data-testid="clerk-provider">{children}</div>
)

export const SignIn = () => <div data-testid="sign-in">Sign In Component</div>

export const SignUp = () => <div data-testid="sign-up">Sign Up Component</div>

export const UserButton = () => <div data-testid="user-button">User Button</div>

export const Protect = ({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) => (
  <div data-testid="clerk-protect">{children}</div>
)

export const SignInButton = ({ children }: { children: React.ReactNode; mode?: string }) => (
  <div data-testid="sign-in-button">{children}</div>
)

export const SignUpButton = ({ children }: { children: React.ReactNode; mode?: string }) => (
  <div data-testid="sign-up-button">{children}</div>
)

export const SignedIn = ({ children }: { children: React.ReactNode }) => (
  <>{children}</>
)

export const SignedOut = ({ children }: { children: React.ReactNode }) => (
  <>{null}</>
)

export const useUser = () => ({
  isSignedIn: true,
  user: {
    id: 'test_user_001',
    emailAddresses: [{ emailAddress: 'test@example.com' }],
    firstName: 'Test',
    lastName: 'User',
    fullName: 'Test User',
  },
  isLoaded: true,
})

export const useAuth = () => ({
  isSignedIn: true,
  isLoaded: true,
  userId: 'test_user_001',
  sessionId: 'test_session',
  getToken: jest.fn().mockResolvedValue('mock_token'),
})

export const useClerk = () => ({
  signOut: jest.fn(),
  openSignIn: jest.fn(),
  openSignUp: jest.fn(),
})

// Mock auth middleware
export const authMiddleware = () => (req: any) => {
  return null
}

// Mock getAuth for API routes
export const getAuth = () => ({
  userId: 'test_user_001',
  sessionId: 'test_session',
})
