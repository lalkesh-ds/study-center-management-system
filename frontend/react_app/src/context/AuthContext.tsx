import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { User, RegisterPayload } from '../types'
import { authApi } from '../api/auth'
import { tokenStorage } from '../utils/tokenStorage'

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string, rememberMe?: boolean) => Promise<User>
  register: (payload: RegisterPayload, rememberMe?: boolean) => Promise<User>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => tokenStorage.getUser())
  const [token, setToken] = useState<string | null>(() => tokenStorage.getToken())
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const verifySession = useCallback(async () => {
    const storedToken = tokenStorage.getToken()
    const storedRefreshToken = tokenStorage.getRefreshToken()

    if (!storedToken && !storedRefreshToken) {
      setUser(null)
      setToken(null)
      setIsLoading(false)
      return
    }

    try {
      // 1. Validate existing access token with backend
      const profile = await authApi.getMe()
      setUser(profile)
      setToken(storedToken)
      tokenStorage.updateUser(profile)
    } catch {
      // 2. If access token verification fails, attempt silent refresh if refresh token exists
      if (storedRefreshToken) {
        try {
          const refreshed = await authApi.refreshToken(storedRefreshToken)
          tokenStorage.updateTokens(refreshed.access_token, refreshed.refresh_token)
          tokenStorage.updateUser(refreshed.user)
          setToken(refreshed.access_token)
          setUser(refreshed.user)
        } catch {
          // Both access token and refresh token failed — clear session completely
          tokenStorage.clearSession()
          setUser(null)
          setToken(null)
        }
      } else {
        tokenStorage.clearSession()
        setUser(null)
        setToken(null)
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    verifySession()

    // Cross-tab synchronization via storage event
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'auth_token' || e.key === 'auth_user') {
        if (!e.newValue) {
          // Token removed in another tab -> sync logout immediately
          setUser(null)
          setToken(null)
        } else {
          // New session established in another tab -> sync session
          verifySession()
        }
      }
    }

    // Custom event triggered by axios interceptor upon token expiration
    const handleSessionExpired = () => {
      setUser(null)
      setToken(null)
      setIsLoading(false)
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('auth:session_expired', handleSessionExpired)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('auth:session_expired', handleSessionExpired)
    }
  }, [verifySession])

  const login = async (username: string, password: string, rememberMe = true): Promise<User> => {
    const res = await authApi.login(username, password)
    tokenStorage.setSession(res.access_token, res.refresh_token, res.user, rememberMe)
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }

  const register = async (payload: RegisterPayload, rememberMe = true): Promise<User> => {
    const res = await authApi.register(payload)
    tokenStorage.setSession(res.access_token, res.refresh_token, res.user, rememberMe)
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }

  const logout = () => {
    const refreshToken = tokenStorage.getRefreshToken()
    // Call server to invalidate refresh token in database
    authApi.logout(refreshToken)

    // Clear local storage and session state
    tokenStorage.clearSession()
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !isLoading && !!token && !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
