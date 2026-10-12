/**
 * Secure Token and Session Storage Abstraction
 * Handles dual-mode persistence:
 * 1. Persistent Session ("Remember Me" = true): uses localStorage (persists across tab/browser closure)
 * 2. Ephemeral Session ("Remember Me" = false): uses sessionStorage (cleared when browser/tab is closed)
 */

import type { User } from '../types'

const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'auth_refresh_token'
const USER_KEY = 'auth_user'
const REMEMBER_KEY = 'auth_remember_me'

export const tokenStorage = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY)
  },

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return sessionStorage.getItem(REFRESH_TOKEN_KEY) || localStorage.getItem(REFRESH_TOKEN_KEY)
  },

  getUser(): User | null {
    if (typeof window === 'undefined') return null
    const raw = sessionStorage.getItem(USER_KEY) || localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as User
    } catch {
      return null
    }
  },

  isRememberMe(): boolean {
    if (typeof window === 'undefined') return false
    return localStorage.getItem(REMEMBER_KEY) === 'true'
  },

  setSession(
    accessToken: string,
    refreshToken?: string | null,
    user?: User | null,
    rememberMe = false
  ): void {
    if (typeof window === 'undefined') return

    const primaryStorage = rememberMe ? localStorage : sessionStorage
    const secondaryStorage = rememberMe ? sessionStorage : localStorage

    // Clean stale keys from alternative storage to prevent dual-state confusion
    secondaryStorage.removeItem(TOKEN_KEY)
    secondaryStorage.removeItem(REFRESH_TOKEN_KEY)
    secondaryStorage.removeItem(USER_KEY)
    secondaryStorage.removeItem(REMEMBER_KEY)

    // Store in selected storage
    primaryStorage.setItem(TOKEN_KEY, accessToken)
    if (refreshToken) {
      primaryStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    }
    if (user) {
      primaryStorage.setItem(USER_KEY, JSON.stringify(user))
    }

    if (rememberMe) {
      localStorage.setItem(REMEMBER_KEY, 'true')
    } else {
      localStorage.removeItem(REMEMBER_KEY)
    }
  },

  updateTokens(accessToken: string, refreshToken?: string | null): void {
    if (typeof window === 'undefined') return

    // Identify which storage currently holds the session
    const isLocal = !!localStorage.getItem(TOKEN_KEY)
    const storage = isLocal ? localStorage : sessionStorage

    storage.setItem(TOKEN_KEY, accessToken)
    if (refreshToken) {
      storage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    }
  },

  updateUser(user: User): void {
    if (typeof window === 'undefined') return
    const isLocal = !!localStorage.getItem(TOKEN_KEY)
    const storage = isLocal ? localStorage : sessionStorage
    storage.setItem(USER_KEY, JSON.stringify(user))
  },

  clearSession(): void {
    if (typeof window === 'undefined') return

    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)
    sessionStorage.removeItem(REMEMBER_KEY)

    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(REMEMBER_KEY)
  },
}
