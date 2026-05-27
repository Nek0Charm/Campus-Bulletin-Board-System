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

  getUnreadCount(): Promise<number> {
    return httpClient.get('/api/v1/notifications/unread-count')
  },

  markRead(id: string): Promise<void> {
    return httpClient.post(`/api/v1/notifications/${id}/read`)
  },

  markAllRead(): Promise<void> {
    return httpClient.post('/api/v1/notifications/read-all')
  },
}
