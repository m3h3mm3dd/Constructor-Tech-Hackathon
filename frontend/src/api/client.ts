import axios from 'axios';

/**
 * Read the API base URL from either localStorage or the environment.
 * LocalStorage overrides environment variables so that the Settings page can
 * configure it at runtime.
 */
function getBaseUrl(): string {
  const stored = localStorage.getItem('apiBaseUrl');
  const env = import.meta.env.VITE_API_BASE_URL || '';
  return stored ?? env;
}

/**
 * Read the internal API key from either localStorage or the environment.
 */
function getApiKey(): string {
  const stored = localStorage.getItem('apiKey');
  const env = import.meta.env.VITE_INTERNAL_API_KEY || '';
  return stored ?? env;
}

/**
 * Create a preconfigured axios instance. We defer reading the base URL and
 * API key until each request via an interceptor so that changes in
 * localStorage are picked up automatically.
 */
export const apiClient = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
});

// Attach an interceptor to set the baseURL and API key header before each request.
apiClient.interceptors.request.use((config) => {
  // Apply the latest base URL from localStorage or env
  config.baseURL = getBaseUrl();
  const apiKey = getApiKey();
  if (apiKey) {
    config.headers = config.headers ?? {};
    // Use the common header name expected by the backend
    (config.headers as Record<string, string>)['X-API-Key'] = apiKey;
  }
  return config;
});

// Error handler utility
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.detail) {
      return error.response.data.detail as string;
    }
    if (error.response?.data?.message) {
      return error.response.data.message as string;
    }
    return error.message;
  }
  return String(error);
}