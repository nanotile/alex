// API configuration that works for both local and production environments
// Use NEXT_PUBLIC_API_URL from environment, with fallback logic for production
export const getApiUrl = () => {
  // First, check if NEXT_PUBLIC_API_URL is set (from .env.local)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // Fallback logic for production (CloudFront setup)
  if (typeof window !== 'undefined') {
    // Client-side: check if we're on localhost
    if (window.location.hostname === 'localhost') {
      return 'http://localhost:8000';
    } else {
      // Production: use relative path (CloudFront handles routing /api/* to API Gateway)
      return '';
    }
  }

  // Server-side during build
  return '';
};

export const API_URL = getApiUrl();