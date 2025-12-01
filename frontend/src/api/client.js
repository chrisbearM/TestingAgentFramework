import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.DEV ? 'http://localhost:8000/api' : '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes (120 seconds) - long timeout for LLM operations
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log('[API Client] Request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      data: config.data,
      headers: config.headers
    })
    return config
  },
  (error) => {
    console.error('[API Client] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('[API Client] Response:', {
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      data: response.data
    })
    return response
  },
  (error) => {
    console.error('[API Client] Response error:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      data: error.response?.data
    })

    if (error.response?.status === 401) {
      console.log('[API Client] 401 Unauthorized - emitting auth-error event')
      // Emit custom event for React app to handle with React Router
      // This prevents hard redirect that breaks SPA navigation
      window.dispatchEvent(new CustomEvent('auth-error', { detail: { status: 401 } }))
    }
    return Promise.reject(error)
  }
)

export default api
