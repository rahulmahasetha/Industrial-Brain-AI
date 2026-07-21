// Resolve the API URL securely for Vercel and local development
const envApiUrl = import.meta.env.VITE_API_URL;
const fallbackApiOrigin = 'https://industrial-brain-ai-zad4.onrender.com';

// If VITE_API_URL ends with /api, API_ORIGIN is the base url without /api
export const API_ORIGIN = envApiUrl 
  ? envApiUrl.replace(/\/api\/?$/, '') 
  : fallbackApiOrigin;

// Ensure API_BASE_URL always has /api
export const API_BASE_URL = envApiUrl 
  ? (envApiUrl.endsWith('/api') || envApiUrl.endsWith('/api/') ? envApiUrl : `${envApiUrl}/api`) 
  : `${fallbackApiOrigin}/api`;
