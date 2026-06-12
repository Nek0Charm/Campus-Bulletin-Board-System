import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types/user'

vi.mock('@/api/auth', () => ({
  authAPI: {
    login: vi.fn<() => void>(),
    register: vi.fn<() => void>(),
    logout: vi.fn<() => void>(),
    resetPassword: vi.fn<() => void>(),
    verifyEmail: vi.fn<() => void>(),
    resendVerification: vi.fn<() => void>(),
  },
}))

vi.mock('@/api/users', () => ({
  usersAPI: {
    getProfile: vi.fn<() => void>(),
    updateProfile: vi.fn<() => void>(),
    getUserStats: vi.fn<() => void>(),
  },
}))

vi.mock('@/utils/storage', () => ({
  getToken: vi.fn<() => null>(() => null),
  setToken: vi.fn<() => void>(),
  removeToken: vi.fn<() => void>(),
}))

import { authAPI } from '@/api/auth'
import { usersAPI } from '@/api/users'
import { getToken, setToken, removeToken } from '@/utils/storage'

const mockUser: User = {
  id: 'user-1',
  username: 'testuser',
  email: 'test@example.com',
  nickname: 'Test User',
  avatar_url: null,
  role: 'user',
  status: 'active',
  email_verified: true,
  muted_until: null,
  last_login_at: '2026-01-01T00:00:00Z',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const mockAdminUser: User = { ...mockUser, id: 'admin-1', role: 'admin', username: 'admin' }

const mockLoginData = {
  access_token: 'test-jwt-token',
  token_type: 'bearer',
  expires_in: 3600,
  user: { id: 'user-1', username: 'testuser', nickname: 'Test User' },
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.mocked(getToken).mockReturnValue(null)
  })

  describe('initial state', () => {
    it('has null token and user when no token in storage', () => {
      const store = useAuthStore()
      expect(store.token).toBeNull()
      expect(store.currentUser).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('loads token from localStorage on creation', () => {
      vi.mocked(getToken).mockReturnValue('stored-token')
      const store = useAuthStore()
      expect(store.token).toBe('stored-token')
      expect(getToken).toHaveBeenCalled()
    })
  })

  describe('getters', () => {
    it('isAuthenticated is false when token is null', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
    })

    it('isAuthenticated is true when token is set', () => {
      const store = useAuthStore()
      store.$patch({ token: 'some-token' })
      expect(store.isAuthenticated).toBe(true)
    })

    it('isAdmin is false for regular user', () => {
      const store = useAuthStore()
      store.$patch({ currentUser: mockUser })
      expect(store.isAdmin).toBe(false)
    })

    it('isAdmin is true for admin user', () => {
      const store = useAuthStore()
      store.$patch({ currentUser: mockAdminUser })
      expect(store.isAdmin).toBe(true)
    })

    it('isAdmin is false when currentUser is null', () => {
      const store = useAuthStore()
      expect(store.isAdmin).toBe(false)
    })

    it('isMuted is false when muted_until is null', () => {
      const store = useAuthStore()
      store.$patch({ currentUser: mockUser })
      expect(store.isMuted).toBe(false)
    })

    it('isMuted is true when muted_until is in the future', () => {
      const store = useAuthStore()
      const future = new Date(Date.now() + 86400000).toISOString()
      store.$patch({ currentUser: { ...mockUser, muted_until: future } })
      expect(store.isMuted).toBe(true)
    })

    it('isMuted is false when muted_until is in the past', () => {
      const store = useAuthStore()
      const past = new Date(Date.now() - 86400000).toISOString()
      store.$patch({ currentUser: { ...mockUser, muted_until: past } })
      expect(store.isMuted).toBe(false)
    })
  })

  describe('login', () => {
    it('successful login sets token and fetches profile', async () => {
      vi.mocked(authAPI.login).mockResolvedValueOnce(mockLoginData)
      vi.mocked(usersAPI.getProfile).mockResolvedValueOnce(mockUser)
      const store = useAuthStore()

      const result = await store.login({ account: 'testuser', password: 'password123' })

      expect(result).toBe(true)
      expect(authAPI.login).toHaveBeenCalledWith({ account: 'testuser', password: 'password123' })
      expect(setToken).toHaveBeenCalledWith('test-jwt-token')
      expect(store.token).toBe('test-jwt-token')
      expect(usersAPI.getProfile).toHaveBeenCalled()
      expect(store.currentUser).toEqual(mockUser)
      expect(store.loading).toBe(false)
    })

    it('login failure does not set token and re-throws', async () => {
      const error = new Error('Invalid credentials')
      vi.mocked(authAPI.login).mockRejectedValueOnce(error)
      const store = useAuthStore()

      await expect(store.login({ account: 'bad', password: 'wrong' })).rejects.toThrow(
        'Invalid credentials',
      )
      expect(store.token).toBeNull()
      expect(store.currentUser).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('login cleans up partial state when fetchProfile fails after token set', async () => {
      vi.mocked(authAPI.login).mockResolvedValueOnce(mockLoginData)
      vi.mocked(usersAPI.getProfile).mockRejectedValueOnce(new Error('Profile fetch failed'))
      const store = useAuthStore()

      await expect(store.login({ account: 'testuser', password: 'password123' })).rejects.toThrow(
        'Profile fetch failed',
      )
      expect(removeToken).toHaveBeenCalled()
      expect(store.token).toBeNull()
    })

    it('login sets loading to true during the call', async () => {
      vi.mocked(authAPI.login).mockResolvedValueOnce(mockLoginData)
      vi.mocked(usersAPI.getProfile).mockResolvedValueOnce(mockUser)
      const store = useAuthStore()

      const promise = store.login({ account: 'testuser', password: 'password123' })
      expect(store.loading).toBe(true)
      await promise
      expect(store.loading).toBe(false)
    })
  })

  describe('register', () => {
    it('successful register returns true', async () => {
      vi.mocked(authAPI.register).mockResolvedValueOnce({ id: 'new-user', username: 'newbie' })
      const store = useAuthStore()

      const result = await store.register({
        username: 'newbie',
        email: 'new@example.com',
        password: 'Password123',
      })

      expect(result).toBe(true)
      expect(authAPI.register).toHaveBeenCalled()
      expect(store.loading).toBe(false)
    })

    it('register sets loading state correctly', async () => {
      vi.mocked(authAPI.register).mockResolvedValueOnce({ id: 'x', username: 'x' })
      const store = useAuthStore()

      const promise = store.register({ username: 'x', email: 'x@x.com', password: 'Pass123' })
      expect(store.loading).toBe(true)
      await promise
      expect(store.loading).toBe(false)
    })

    it('register failure sets loading to false', async () => {
      vi.mocked(authAPI.register).mockRejectedValueOnce(new Error('dup'))
      const store = useAuthStore()

      await expect(
        store.register({ username: 'x', email: 'x@x.com', password: 'Pass123' }),
      ).rejects.toThrow('dup')
      expect(store.loading).toBe(false)
    })
  })

  describe('logout', () => {
    it('calls API, removes token and clears user', async () => {
      vi.mocked(authAPI.logout).mockResolvedValueOnce(undefined as never)
      const store = useAuthStore()
      store.$patch({ token: 'some-token', currentUser: mockUser })

      await store.logout()

      expect(authAPI.logout).toHaveBeenCalled()
      expect(removeToken).toHaveBeenCalled()
      expect(store.token).toBeNull()
      expect(store.currentUser).toBeNull()
    })

    it('still clears local state when API call fails', async () => {
      vi.mocked(authAPI.logout).mockRejectedValueOnce(new Error('network'))
      const store = useAuthStore()
      store.$patch({ token: 'some-token', currentUser: mockUser })

      await store.logout()

      expect(removeToken).toHaveBeenCalled()
      expect(store.token).toBeNull()
      expect(store.currentUser).toBeNull()
    })
  })

  describe('fetchProfile', () => {
    it('sets currentUser on success', async () => {
      vi.mocked(usersAPI.getProfile).mockResolvedValueOnce(mockUser)
      const store = useAuthStore()

      await store.fetchProfile()

      expect(store.currentUser).toEqual(mockUser)
    })

    it('clears token and user on 401 response', async () => {
      const err = { response: { status: 401 } }
      vi.mocked(usersAPI.getProfile).mockRejectedValueOnce(err)
      const store = useAuthStore()
      store.$patch({ token: 'some-token' })

      await expect(store.fetchProfile()).rejects.toEqual(err)
      expect(removeToken).toHaveBeenCalled()
      expect(store.token).toBeNull()
      expect(store.currentUser).toBeNull()
    })

    it('clears token and user on 403 response', async () => {
      const err = { response: { status: 403 } }
      vi.mocked(usersAPI.getProfile).mockRejectedValueOnce(err)
      const store = useAuthStore()
      store.$patch({ token: 'some-token' })

      await expect(store.fetchProfile()).rejects.toEqual(err)
      expect(removeToken).toHaveBeenCalled()
      expect(store.token).toBeNull()
    })

    it('re-throws but keeps token on other errors', async () => {
      const err = { response: { status: 500 } }
      vi.mocked(usersAPI.getProfile).mockRejectedValueOnce(err)
      const store = useAuthStore()
      store.$patch({ token: 'some-token' })

      await expect(store.fetchProfile()).rejects.toEqual(err)
      expect(store.token).toBe('some-token')
      expect(removeToken).not.toHaveBeenCalled()
    })
  })

  describe('restoreSession', () => {
    it('no-ops when there is no token', async () => {
      const store = useAuthStore()
      await store.restoreSession()
      expect(usersAPI.getProfile).not.toHaveBeenCalled()
    })

    it('fetches profile when token exists', async () => {
      vi.mocked(usersAPI.getProfile).mockResolvedValueOnce(mockUser)
      const store = useAuthStore()
      store.$patch({ token: 'stored-token' })

      await store.restoreSession()

      expect(usersAPI.getProfile).toHaveBeenCalled()
      expect(store.currentUser).toEqual(mockUser)
    })

    it('swallows error on transient failure (does not clear token)', async () => {
      vi.mocked(usersAPI.getProfile).mockRejectedValueOnce(new Error('network down'))
      const store = useAuthStore()
      store.$patch({ token: 'stored-token' })

      await store.restoreSession()

      expect(store.token).toBe('stored-token')
      expect(store.currentUser).toBeNull()
    })
  })
})
