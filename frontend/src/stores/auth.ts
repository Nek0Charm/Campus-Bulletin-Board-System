import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api/auth'
import { usersAPI } from '@/api/users'
import { getToken, setToken, removeToken } from '@/utils/storage'
import type { User, LoginRequest, RegisterRequest } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getToken())
  const currentUser = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')
  const isMuted = computed(() => {
    if (!currentUser.value?.muted_until) return false
    return new Date(currentUser.value.muted_until) > new Date()
  })

  async function login(payload: LoginRequest) {
    loading.value = true
    try {
      const data = await authAPI.login(payload)
      setToken(data.access_token)
      token.value = data.access_token
      await fetchProfile()
      return true
    } catch (err) {
      // Clean up any partially-set state on failure
      if (token.value) {
        removeToken()
        token.value = null
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterRequest) {
    loading.value = true
    try {
      await authAPI.register(payload)
      return true
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authAPI.logout()
    } catch {
      // ignore logout api errors
    }
    removeToken()
    token.value = null
    currentUser.value = null
  }

  async function fetchProfile() {
    try {
      currentUser.value = await usersAPI.getProfile()
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 401 || status === 403) {
        removeToken()
        token.value = null
        currentUser.value = null
      }
      throw err
    }
  }

  async function restoreSession() {
    if (!token.value) return
    try {
      await fetchProfile()
    } catch {
      // transient error — token not cleared, session can recover
    }
  }

  return {
    token,
    currentUser,
    loading,
    isAuthenticated,
    isAdmin,
    isMuted,
    login,
    register,
    logout,
    fetchProfile,
    restoreSession,
  }
})
