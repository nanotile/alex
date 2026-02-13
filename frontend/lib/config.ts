// API configuration that works for both local and production environments
// Use NEXT_PUBLIC_API_URL from environment, with fallback logic for production
// Production API Gateway URL
const API_GATEWAY_URL = 'https://0b75gjui0j.execute-api.us-east-1.amazonaws.com';

export const getApiUrl = (): string => {
  // Client-side: determine API URL based on hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    // Localhost (any port) - use local API server
    // This includes direct access and VS Code port forwarding
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }

    // Production/remote access - use API Gateway
    return API_GATEWAY_URL;
  }

  // Server-side during build
  return 'http://localhost:8000';
};

// Make this a getter so it's evaluated fresh each time
export const API_URL = typeof window !== 'undefined' ? getApiUrl() : 'http://localhost:8000';