import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const globalLoading = ref(false)
  const sidebarCollapsed = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setGlobalLoading(val: boolean) {
    globalLoading.value = val
  }

  return {
    globalLoading,
    sidebarCollapsed,
    toggleSidebar,
    setGlobalLoading,
  }
})
