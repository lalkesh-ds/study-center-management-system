import { apiClient } from './client'
import type { LoginResponse, User, RegisterPayload } from '../types'

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', { username, password })
    return data
  },
  register: async (payload: RegisterPayload): Promise<LoginResponse> => {
    const { data } = await apiClient.post<LoginResponse>('/auth/register', payload)
    return data
  },
  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  },
  refreshToken: async (refreshToken: string): Promise<LoginResponse> => {
    const { data } = await apiClient.post<LoginResponse>('/auth/refresh', { refresh_token: refreshToken })
    return data
  },
  logout: async (refreshToken?: string | null): Promise<void> => {
    if (refreshToken) {
      await apiClient.post('/auth/logout', { refresh_token: refreshToken }).catch(() => {})
    } else {
      await apiClient.post('/auth/logout').catch(() => {})
    }
  },
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
  listUsers: async (skip = 0, limit = 50): Promise<User[]> => {
    const { data } = await apiClient.get<User[]>('/auth/users', { params: { skip, limit } })
    return data
  },
}
