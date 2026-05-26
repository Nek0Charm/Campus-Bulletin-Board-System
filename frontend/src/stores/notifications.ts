import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { notificationsAPI } from '@/api/notifications'
import type { NotificationRead } from '@/types/notification'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<NotificationRead[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const pagination = reactive({
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
    total: 0,
    totalPages: 0,
  })

  let pollTimer: ReturnType<typeof setInterval> | null = null

  async function fetchNotifications(page = 1, pageSize = DEFAULT_PAGE_SIZE) {
    loading.value = true
    try {
      const data = await notificationsAPI.getNotifications({ page, page_size: pageSize })
      notifications.value = data.items
      Object.assign(pagination, data.pagination)
    } finally {
      loading.value = false
    }
  }

  async function fetchUnreadCount() {
    try {
      unreadCount.value = await notificationsAPI.getUnreadCount()
    } catch {
      // silent
    }
  }

  async function markRead(id: string) {
    await notificationsAPI.markRead(id)
    const item = notifications.value.find((n) => n.id === id)
    if (item) {
      item.is_read = true
      item.read_at = new Date().toISOString()
    }
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  async function markAllRead() {
    await notificationsAPI.markAllRead()
    notifications.value.forEach((n) => {
      n.is_read = true
      n.read_at = new Date().toISOString()
    })
    unreadCount.value = 0
  }

  function startPolling() {
    stopPolling()
    fetchUnreadCount()
    pollTimer = setInterval(fetchUnreadCount, 30000)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    notifications,
    unreadCount,
    loading,
    pagination,
    fetchNotifications,
    fetchUnreadCount,
    markRead,
    markAllRead,
    startPolling,
    stopPolling,
  }
})
