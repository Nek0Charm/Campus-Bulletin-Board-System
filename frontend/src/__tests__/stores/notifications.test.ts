import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNotificationStore } from '@/stores/notifications'
import type { NotificationRead } from '@/types/notification'
import type { PaginatedData } from '@/types/api'

vi.mock('@/api/notifications', () => ({
  notificationsAPI: {
    getNotifications: vi.fn<() => void>(),
    getUnreadCount: vi.fn<() => void>(),
    markRead: vi.fn<() => void>(),
    markAllRead: vi.fn<() => void>(),
  },
}))

import { notificationsAPI } from '@/api/notifications'

function makeMockNotification(overrides: Partial<NotificationRead> = {}): NotificationRead {
  return {
    id: 'notif-1',
    recipient_id: 'user-1',
    type: 'comment',
    actor: {
      id: 'user-2',
      username: 'commenter',
      nickname: 'Commenter',
      avatar_url: undefined,
    },
    title: '新评论',
    related_type: 'post',
    related_id: 'post-1',
    content: '评论了你的帖子',
    is_read: false,
    read_at: undefined,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function makePaginated<T>(items: T[], page = 1, pageSize = 20): PaginatedData<T> {
  return {
    items,
    pagination: {
      page,
      page_size: pageSize,
      total: items.length,
      total_pages: Math.ceil(items.length / pageSize),
    },
  }
}

describe('useNotificationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    // Ensure all timers are cleaned up
    vi.useRealTimers()
  })

  it('has correct initial state', () => {
    const store = useNotificationStore()
    expect(store.notifications).toEqual([])
    expect(store.unreadCount).toBe(0)
    expect(store.loading).toBe(false)
    expect(store.pagination.total).toBe(0)
  })

  describe('fetchNotifications', () => {
    it('loads notifications and updates pagination', async () => {
      const items = [makeMockNotification(), makeMockNotification({ id: 'notif-2' })]
      vi.mocked(notificationsAPI.getNotifications).mockResolvedValueOnce(makePaginated(items))
      const store = useNotificationStore()

      await store.fetchNotifications(1)

      expect(notificationsAPI.getNotifications).toHaveBeenCalledWith({ page: 1, page_size: 20 })
      expect(store.notifications).toEqual(items)
      expect(store.pagination.total).toBe(2)
      expect(store.loading).toBe(false)
    })

    it('uses custom page and pageSize', async () => {
      vi.mocked(notificationsAPI.getNotifications).mockResolvedValueOnce(makePaginated([]))
      const store = useNotificationStore()

      await store.fetchNotifications(3, 10)

      expect(notificationsAPI.getNotifications).toHaveBeenCalledWith({ page: 3, page_size: 10 })
    })
  })

  describe('fetchUnreadCount', () => {
    it('updates unreadCount from API', async () => {
      vi.mocked(notificationsAPI.getUnreadCount).mockResolvedValueOnce(5 as never)
      const store = useNotificationStore()

      await store.fetchUnreadCount()

      expect(store.unreadCount).toBe(5)
    })

    it('silently handles API error', async () => {
      vi.mocked(notificationsAPI.getUnreadCount).mockRejectedValueOnce(new Error('network'))
      const store = useNotificationStore()
      store.$patch({ unreadCount: 3 })

      await store.fetchUnreadCount()

      expect(store.unreadCount).toBe(3) // unchanged
    })
  })

  describe('markRead', () => {
    it('calls API, optimistically marks as read and decrements unreadCount', async () => {
      vi.mocked(notificationsAPI.markRead).mockResolvedValueOnce(undefined as never)
      const store = useNotificationStore()
      const notif = makeMockNotification({ id: 'n1', is_read: false })
      store.$patch({ notifications: [notif], unreadCount: 3 })

      await store.markRead('n1')

      expect(notificationsAPI.markRead).toHaveBeenCalledWith('n1')
      expect(store.notifications[0]!.is_read).toBe(true)
      expect(store.notifications[0]!.read_at).toBeTruthy()
      expect(store.unreadCount).toBe(2)
    })

    it('does not decrement unreadCount below 0', async () => {
      vi.mocked(notificationsAPI.markRead).mockResolvedValueOnce(undefined as never)
      const store = useNotificationStore()
      const notif = makeMockNotification({ id: 'n1', is_read: false })
      store.$patch({ notifications: [notif], unreadCount: 0 })

      await store.markRead('n1')

      expect(store.unreadCount).toBe(0)
    })

    it('no-ops when notification not found in local list', async () => {
      vi.mocked(notificationsAPI.markRead).mockResolvedValueOnce(undefined as never)
      const store = useNotificationStore()
      store.$patch({ unreadCount: 1 })

      await store.markRead('nonexistent')

      expect(store.unreadCount).toBe(0) // still decremented
    })
  })

  describe('markAllRead', () => {
    it('calls API, marks all as read and resets unreadCount', async () => {
      vi.mocked(notificationsAPI.markAllRead).mockResolvedValueOnce(undefined as never)
      const store = useNotificationStore()
      const items = [
        makeMockNotification({ id: 'n1', is_read: false }),
        makeMockNotification({ id: 'n2', is_read: false }),
        makeMockNotification({ id: 'n3', is_read: true }),
      ]
      store.$patch({ notifications: items, unreadCount: 2 })

      await store.markAllRead()

      expect(notificationsAPI.markAllRead).toHaveBeenCalled()
      expect(store.notifications.every((n) => n.is_read)).toBe(true)
      expect(store.notifications.every((n) => !!n.read_at)).toBe(true)
      expect(store.unreadCount).toBe(0)
    })
  })

  describe('polling lifecycle', () => {
    it('startPolling calls fetchUnreadCount immediately', () => {
      vi.mocked(notificationsAPI.getUnreadCount).mockResolvedValueOnce(3 as never)
      const store = useNotificationStore()

      store.startPolling()

      expect(notificationsAPI.getUnreadCount).toHaveBeenCalledTimes(1)
    })

    it('startPolling sets up interval timer', () => {
      vi.mocked(notificationsAPI.getUnreadCount).mockResolvedValue(0 as never)
      const store = useNotificationStore()

      store.startPolling()

      // Advance by 30s — the interval should fire
      vi.advanceTimersByTime(30000)
      expect(notificationsAPI.getUnreadCount).toHaveBeenCalledTimes(2) // initial + interval
    })

    it('stopPolling clears the interval', () => {
      vi.mocked(notificationsAPI.getUnreadCount).mockResolvedValue(0 as never)
      const store = useNotificationStore()

      store.startPolling()
      store.stopPolling()

      vi.advanceTimersByTime(30000)
      expect(notificationsAPI.getUnreadCount).toHaveBeenCalledTimes(1) // initial only
    })

    it('startPolling twice does not create duplicate timers', () => {
      vi.mocked(notificationsAPI.getUnreadCount).mockResolvedValue(0 as never)
      const store = useNotificationStore()

      store.startPolling()
      store.startPolling()

      vi.advanceTimersByTime(30000)
      // Initial + 1 interval (not 2 initial + 2 intervals)
      // startPolling calls stopPolling first, so old interval is cleared
      // then it calls fetchUnreadCount immediately (second time)
      // then sets up ONE new interval
      // So after 30s: 2 initial calls + 1 interval = 3
      expect(notificationsAPI.getUnreadCount).toHaveBeenCalledTimes(3)
    })
  })
})
