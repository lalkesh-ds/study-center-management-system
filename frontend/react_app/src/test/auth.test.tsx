import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { authApi } from '../api/auth'

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
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
      <button onClick={() => login('admin', 'Admin@123')}>Login Action</button>
      <button onClick={logout}>Logout Action</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
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

  it('logs in successfully and updates authentication state', async () => {
    const user = userEvent.setup()
    const mockUser = {
      user_id: 1,
      username: 'admin',
      email: 'admin@library.local',
      full_name: 'Admin User',
      role: 'ADMIN' as const,
      is_active: true,
      created_at: '2026-01-01',
    }

    vi.mocked(authApi.login).mockResolvedValueOnce({
      access_token: 'fake-jwt-token',
      token_type: 'bearer',
      user: mockUser,
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    const loginBtn = await screen.findByRole('button', { name: /Login Action/i })
    await user.click(loginBtn)

    expect(screen.getByTestId('auth-status')).toHaveTextContent('logged-in')
    expect(screen.getByTestId('username')).toHaveTextContent('admin')
    expect(localStorage.getItem('auth_token')).toBe('fake-jwt-token')
  })

  it('logs out and clears localStorage', async () => {
    const user = userEvent.setup()
    const mockUser = {
      user_id: 2,
      username: 'librarian',
      email: 'lib@test.com',
      full_name: 'Librarian User',
      role: 'OPERATOR' as const,
      is_active: true,
      created_at: '2026-01-01',
    }

    localStorage.setItem('auth_token', 'existing-token')
    localStorage.setItem('auth_user', JSON.stringify(mockUser))

    vi.mocked(authApi.getMe).mockResolvedValueOnce(mockUser)

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
    expect(localStorage.getItem('auth_user')).toBeNull()
  })
})
