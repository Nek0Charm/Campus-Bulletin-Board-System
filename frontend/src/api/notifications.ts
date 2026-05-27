import httpClient from './client'
import type { NotificationRead } from '@/types/notification'
import type { PaginatedData } from '@/types/api'

export const notificationsAPI = {
  getNotifications(params?: {
    page?: number
    page_size?: number
  }): Promise<PaginatedData<NotificationRead>> {
    return httpClient.get('/api/v1/notifications/', { params })
  },

  async getUnreadCount(): Promise<number> {
    const result = (await httpClient.get('/api/v1/notifications/unread-count')) as {
      unread_count: number
    }
    return result.unread_count
  },

  markRead(id: string): Promise<void> {
    return httpClient.put(`/api/v1/notifications/${id}/read`)
  },

  markAllRead(): Promise<void> {
    return httpClient.put('/api/v1/notifications/read-all')
  },
}
