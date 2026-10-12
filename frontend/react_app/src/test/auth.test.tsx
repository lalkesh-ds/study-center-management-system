import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { authApi } from '../api/auth'

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
    refreshToken: vi.fn(),
    logout: vi.fn(),
  },
}))

const TestConsumer = () => {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth()
  if (isLoading) {
    return <div>Loading auth...</div>
  }
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'logged-in' : 'logged-out'}</div>
      <div data-testid="username">{user?.username || 'none'}</div>
      <button onClick={() => login('admin', 'Admin@123', true)}>Login Action (Remember Me)</button>
      <button onClick={() => login('admin', 'Admin@123', false)}>Login Action (Session Only)</button>
      <button onClick={logout}>Logout Action</button>
    </div>
  )
}

describe('AuthContext & Session Lifecycle', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    vi.clearAllMocks()
  })

  it('initializes as unauthenticated when no token is present', async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    expect(await screen.findByTestId('auth-status')).toHaveTextContent('logged-out')
    expect(screen.getByTestId('username')).toHaveTextContent('none')
  })

  it('logs in with Remember Me (persists to localStorage)', async () => {
    const user = userEvent.setup()
    const mockUser: any = {
      id: '11111111-1111-1111-1111-111111111111',
      username: 'admin',
      email: 'admin@library.local',
      full_name: 'Admin User',
      role: 'ADMIN',
      is_active: true,
      created_at: '2026-01-01',
    }

    vi.mocked(authApi.login).mockResolvedValueOnce({
      access_token: 'fake-jwt-token',
      refresh_token: 'fake-refresh-token',
      token_type: 'bearer',
      user: mockUser,
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    const loginBtn = await screen.findByRole('button', { name: /Login Action \(Remember Me\)/i })
    await user.click(loginBtn)

    expect(screen.getByTestId('auth-status')).toHaveTextContent('logged-in')
    expect(screen.getByTestId('username')).toHaveTextContent('admin')
    expect(localStorage.getItem('auth_token')).toBe('fake-jwt-token')
    expect(localStorage.getItem('auth_refresh_token')).toBe('fake-refresh-token')
    expect(sessionStorage.getItem('auth_token')).toBeNull()
  })

  it('logs in without Remember Me (persists to sessionStorage only)', async () => {
    const user = userEvent.setup()
    const mockUser: any = {
      id: '22222222-2222-2222-2222-222222222222',
      username: 'session_user',
      email: 'session@test.com',
      full_name: 'Session User',
      role: 'ADMIN',
      is_active: true,
      created_at: '2026-01-01',
    }

    vi.mocked(authApi.login).mockResolvedValueOnce({
      access_token: 'session-jwt-token',
      refresh_token: 'session-refresh-token',
      token_type: 'bearer',
      user: mockUser,
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    const loginBtn = await screen.findByRole('button', { name: /Login Action \(Session Only\)/i })
    await user.click(loginBtn)

    expect(screen.getByTestId('auth-status')).toHaveTextContent('logged-in')
    expect(sessionStorage.getItem('auth_token')).toBe('session-jwt-token')
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('logs out and clears all storage and server session', async () => {
    const user = userEvent.setup()
    const mockUser: any = {
      id: '33333333-3333-3333-3333-333333333333',
      username: 'librarian',
      email: 'lib@test.com',
      full_name: 'Librarian User',
      role: 'STAFF',
      is_active: true,
      created_at: '2026-01-01',
    }

    localStorage.setItem('auth_token', 'existing-token')
    localStorage.setItem('auth_refresh_token', 'existing-refresh-token')
    localStorage.setItem('auth_user', JSON.stringify(mockUser))

    vi.mocked(authApi.getMe).mockResolvedValueOnce(mockUser)
    vi.mocked(authApi.logout).mockResolvedValueOnce()

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    expect(await screen.findByTestId('auth-status')).toHaveTextContent('logged-in')

    const logoutBtn = screen.getByRole('button', { name: /Logout Action/i })
    await user.click(logoutBtn)

    expect(screen.getByTestId('auth-status')).toHaveTextContent('logged-out')
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(localStorage.getItem('auth_refresh_token')).toBeNull()
    expect(authApi.logout).toHaveBeenCalledWith('existing-refresh-token')
  })
})
