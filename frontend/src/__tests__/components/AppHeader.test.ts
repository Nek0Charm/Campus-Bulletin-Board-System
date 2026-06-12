import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountWithSetup } from '../setup'
import AppHeader from '@/components/common/AppHeader.vue'
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

const mockRoute = { query: {} as Record<string, string> }
const mockRouter = { push: vi.fn<() => void>(), replace: vi.fn<() => void>() }

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => mockRouter,
}))

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

const mockAdminUser: User = {
  ...mockUser,
  id: 'admin-1',
  role: 'admin',
  username: 'admin',
  nickname: 'Admin',
}

describe('AppHeader', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockRoute.query = {}
  })

  function mountHeader() {
    return mountWithSetup(AppHeader, {
      global: {
        mocks: { $router: mockRouter, $route: mockRoute },
      },
    })
  }

  describe('guest user', () => {
    it('shows login button when not authenticated', () => {
      const wrapper = mountHeader()
      const loginBtn = wrapper.find('.el-button')
      expect(loginBtn.exists()).toBe(true)
      expect(loginBtn.text()).toBe('登录')
    })

    it('does not show user dropdown when not authenticated', () => {
      const wrapper = mountHeader()
      expect(wrapper.find('.el-dropdown').exists()).toBe(false)
    })
  })

  describe('authenticated user', () => {
    beforeEach(() => {
      const authStore = useAuthStore()
      authStore.$patch({ token: 'some-token', currentUser: mockUser })
    })

    it('shows user dropdown with username', () => {
      const wrapper = mountHeader()
      expect(wrapper.find('.el-dropdown').exists()).toBe(true)
      expect(wrapper.find('.username').text()).toBe('Test User')
    })

    it('does not show login button', () => {
      const wrapper = mountHeader()
      expect(wrapper.find('.el-button').exists()).toBe(false)
    })

    it('hides admin link for non-admin users', () => {
      const wrapper = mountHeader()
      // admin link (管理后台) should not be present for regular user
      const items = wrapper.findAll('.el-dropdown-item')
      const texts = items.map((item) => item.text())
      expect(texts.some((t) => t.includes('管理后台'))).toBe(false)
    })
  })

  describe('admin user', () => {
    beforeEach(() => {
      const authStore = useAuthStore()
      authStore.$patch({ token: 'admin-token', currentUser: mockAdminUser })
    })

    it('shows admin link for admin users', () => {
      const wrapper = mountHeader()
      const items = wrapper.findAll('.el-dropdown-item')
      const texts = items.map((item) => item.text())
      expect(texts.some((t) => t.includes('管理后台'))).toBe(true)
    })
  })

  describe('search', () => {
    it('syncs searchKeyword from route.query.q on mount', () => {
      mockRoute.query = { q: 'hello world' }
      const wrapper = mountHeader()
      const input = wrapper.find('.el-input')
      expect(input.attributes('value')).toBe('hello world')
    })

    it('clears searchKeyword when route has no q param', () => {
      mockRoute.query = {}
      const wrapper = mountHeader()
      const input = wrapper.find('.el-input')
      expect(input.attributes('value')).toBe('')
    })

    it('handleSearch can be triggered via enter key', async () => {
      const wrapper = mountHeader()

      // Set the search keyword directly on the component's ref
      const input = wrapper.find('.el-input')
      const inputEl = wrapper.findComponent('.el-input')
      await inputEl.vm.$emit('update:modelValue', 'test query')

      // Trigger the enter key to search
      await inputEl.vm.$emit('keyup', new KeyboardEvent('keyup', { key: 'Enter' }))

      expect(input.attributes('value')).toBe('test query')
    })
  })

  describe('logout', () => {
    it('logout clears auth and navigates home', async () => {
      const authStore = useAuthStore()
      authStore.$patch({ token: 'some-token', currentUser: mockUser })

      const wrapper = mountHeader()

      // Find the logout dropdown item and click it
      const dropdownItems = wrapper.findAll('.el-dropdown-item')
      // Items: 个人中心, 通知, 管理后台 (if admin), 退出登录
      const logoutIdx = dropdownItems.length - 1 // Last item is always logout
      await dropdownItems[logoutIdx].trigger('click')

      // Wait for async handleLogout to complete
      await new Promise((r) => setTimeout(r, 10))

      // After logout, auth state should be reset and router.push called
      expect(authStore.token).toBeNull()
      expect(mockRouter.push).toHaveBeenCalledWith('/')
    })
  })
})
