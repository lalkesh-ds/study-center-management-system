import axios, { AxiosError } from 'axios'

const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (typeof window !== 'undefined' && window.location.hostname && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    // If accessing from LAN IP (e.g. 192.168.0.197), connect to same host backend
    return `http://${window.location.hostname}:8000/api/v1`
  }
  return envUrl || 'http://localhost:8000/api/v1'
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Request Interceptor: Attach JWT Bearer Token if present
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response Interceptor: Format error messages and handle 401
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string; detail?: any; error_code?: string }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }

    let message = 'An unexpected error occurred'
    const data: any = error.response?.data
    if (data) {
      if (data.error) {
        if (typeof data.error.message === 'string') {
          message = data.error.message
        }
        if (data.error.details?.validation_errors && Array.isArray(data.error.details.validation_errors)) {
          const valDetails = data.error.details.validation_errors
            .map((v: any) => `${v.field ? v.field + ': ' : ''}${v.message}`)
            .join('; ')
          message = `${message} (${valDetails})`
        }
      } else if (typeof data.message === 'string') {
        message = data.message
      } else if (typeof data.detail === 'string') {
        message = data.detail
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(', ')
      } else if (typeof data === 'string') {
        message = data
      }
    } else if (error.message) {
      message = error.message
    }

    return Promise.reject(new Error(message))
  }
)
