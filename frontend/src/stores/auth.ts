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

  async function login(payload: LoginRequest) {
    loading.value = true
    try {
      const data = await authAPI.login(payload)
      setToken(data.access_token)
      token.value = data.access_token
      await fetchProfile()
      return true
    } catch {
      return false
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
    login,
    register,
    logout,
    fetchProfile,
    restoreSession,
  }
})
