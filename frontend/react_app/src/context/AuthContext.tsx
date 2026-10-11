import React, { createContext, useContext, useState, useEffect } from 'react'
import type { User } from '../types'
import { authApi } from '../api/auth'

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<User>
  register: (payload: import('../types').RegisterPayload) => Promise<User>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('auth_user')
    return saved ? JSON.parse(saved) : null
  })
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'))
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('auth_token')
      if (storedToken) {
        try {
          const profile = await authApi.getMe()
          setUser(profile)
          localStorage.setItem('auth_user', JSON.stringify(profile))
        } catch {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_refresh_token')
          localStorage.removeItem('auth_user')
          setUser(null)
          setToken(null)
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (username: string, password: string): Promise<User> => {
    const res = await authApi.login(username, password)
    localStorage.setItem('auth_token', res.access_token)
    if (res.refresh_token) {
      localStorage.setItem('auth_refresh_token', res.refresh_token)
    }
    localStorage.setItem('auth_user', JSON.stringify(res.user))
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }

  const register = async (payload: import('../types').RegisterPayload): Promise<User> => {
    const res = await authApi.register(payload)
    localStorage.setItem('auth_token', res.access_token)
    if (res.refresh_token) {
      localStorage.setItem('auth_refresh_token', res.refresh_token)
    }
    localStorage.setItem('auth_user', JSON.stringify(res.user))
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }

  const logout = () => {
    const refreshToken = localStorage.getItem('auth_refresh_token')
    if (refreshToken) {
      authApi.logout(refreshToken).catch(() => {})
    }
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_refresh_token')
    localStorage.removeItem('auth_user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
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
