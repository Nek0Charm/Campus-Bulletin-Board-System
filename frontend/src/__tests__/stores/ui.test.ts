import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUIStore } from '@/stores/ui'

describe('useUIStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('has correct initial state', () => {
    const store = useUIStore()
    expect(store.globalLoading).toBe(false)
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('toggleSidebar toggles sidebarCollapsed', () => {
    const store = useUIStore()
    expect(store.sidebarCollapsed).toBe(false)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('setGlobalLoading(true) sets globalLoading to true', () => {
    const store = useUIStore()
    store.setGlobalLoading(true)
    expect(store.globalLoading).toBe(true)
  })

  it('setGlobalLoading(false) sets globalLoading to false', () => {
    const store = useUIStore()
    store.setGlobalLoading(true)
    store.setGlobalLoading(false)
    expect(store.globalLoading).toBe(false)
  })

  it('toggleSidebar called multiple times alternates correctly', () => {
    const store = useUIStore()
    store.toggleSidebar()
    store.toggleSidebar()
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
  })
})
