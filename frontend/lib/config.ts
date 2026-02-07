// API configuration that works for both local and production environments
// Use NEXT_PUBLIC_API_URL from environment, with fallback logic for production
// Production API Gateway URL
const API_GATEWAY_URL = 'https://0b75gjui0j.execute-api.us-east-1.amazonaws.com';

export const getApiUrl = (): string => {
  // Client-side: always use API Gateway for remote access
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    console.log('getApiUrl: Client-side, hostname:', hostname, 'port:', port);

    // True localhost only - direct browser on the same machine
    if ((hostname === 'localhost' || hostname === '127.0.0.1') &&
        (port === '3000' || port === '3004' || port === '3005' || port === '')) {
      console.log('getApiUrl: True localhost, using http://localhost:8000');
      return 'http://localhost:8000';
    }

    // Everything else (VS Code port forward, remote access, production) - use API Gateway
    console.log('getApiUrl: Using API Gateway:', API_GATEWAY_URL);
    return API_GATEWAY_URL;
  }

  // Server-side during build
  return 'http://localhost:8000';
};

// Make this a getter so it's evaluated fresh each time
export const API_URL = typeof window !== 'undefined' ? getApiUrl() : 'http://localhost:8000';