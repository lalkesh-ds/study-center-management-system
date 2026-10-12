import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { tokenStorage } from '../utils/tokenStorage'

const getApiBaseUrl = (): string => {
  // 1. Production / Render: always use explicit env var if set
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl) return envUrl

  // 2. Local LAN access (e.g. 192.168.x.x) — connect to same host backend on port 8000
  if (
    typeof window !== 'undefined' &&
    window.location.hostname &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1'
  ) {
    return `http://${window.location.hostname}:8000/api/v1`
  }

  // 3. Local dev fallback
  return 'http://localhost:8000/api/v1'
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Request Interceptor: Attach JWT Bearer Token if present in unified storage
apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Token Refresh Mutex / Queue state
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: any) => void
}> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
    } else if (token) {
      promise.resolve(token)
    }
  })
  failedQueue = []
}

// Response Interceptor: Format error messages and handle 401 with silent token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ message?: string; detail?: any; error?: any }>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // If 401 and request is not already retried and not an auth attempt
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      const refreshToken = tokenStorage.getRefreshToken()

      if (refreshToken) {
        if (isRefreshing) {
          // Another request is already refreshing, wait for it
          try {
            const newToken = await new Promise<string>((resolve, reject) => {
              failedQueue.push({ resolve, reject })
            })
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return apiClient(originalRequest)
          } catch (err) {
            return Promise.reject(err)
          }
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
          // Direct call to refresh without using apiClient interceptor recursion
          const refreshUrl = `${getApiBaseUrl()}/auth/refresh`
          const refreshResponse = await axios.post<{
            access_token: string
            refresh_token?: string
          }>(refreshUrl, { refresh_token: refreshToken })

          const newAccessToken = refreshResponse.data.access_token
          const newRefreshToken = refreshResponse.data.refresh_token || refreshToken

          tokenStorage.updateTokens(newAccessToken, newRefreshToken)
          processQueue(null, newAccessToken)

          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return apiClient(originalRequest)
        } catch (refreshErr) {
          processQueue(refreshErr, null)
          tokenStorage.clearSession()
          // Broadcast session expiration across tabs and app
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new Event('auth:session_expired'))
            if (!window.location.pathname.includes('/login')) {
              window.location.href = '/login'
            }
          }
          return Promise.reject(new Error('Session expired. Please sign in again.'))
        } finally {
          isRefreshing = false
        }
      } else {
        // No refresh token available, clear session
        tokenStorage.clearSession()
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.dispatchEvent(new Event('auth:session_expired'))
          window.location.href = '/login'
        }
      }
    }

    // Standardized error message extraction
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
