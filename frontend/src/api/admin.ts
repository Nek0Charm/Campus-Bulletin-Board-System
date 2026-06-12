import httpClient from './client'
import type { User } from '@/types/user'
import type { PaginatedData } from '@/types/api'
import type { BoardMasterInfo } from '@/types/board'
import type { AnnouncementRead } from '@/types/announcement'

export interface AdminStats {
  total_users: number
  total_posts: number
  total_comments: number
  new_posts_today: number
}

export const adminAPI = {
  getStats(): Promise<AdminStats> {
    return httpClient.get('/api/v1/admin/stats')
  },

  listUsers(params?: {
    page?: number
    page_size?: number
    search?: string
    role?: string
    status?: string
  }): Promise<PaginatedData<User>> {
    return httpClient.get('/api/v1/admin/users', { params })
  },

  updateUserStatus(userId: string, status: string): Promise<User> {
    return httpClient.patch(`/api/v1/admin/users/${userId}/status`, { status })
  },

  // Board master management
  listBoardMasters(boardId: string): Promise<BoardMasterInfo[]> {
    return httpClient.get(`/api/v1/admin/boards/${boardId}/masters`)
  },

  addBoardMaster(boardId: string, userId: string): Promise<BoardMasterInfo> {
    return httpClient.post(`/api/v1/admin/boards/${boardId}/masters`, { user_id: userId })
  },

  removeBoardMaster(boardId: string, userId: string): Promise<void> {
    return httpClient.delete(`/api/v1/admin/boards/${boardId}/masters/${userId}`)
  },

  // Mute management
  muteUser(userId: string, durationMinutes: number): Promise<User> {
    return httpClient.post(`/api/v1/admin/users/${userId}/mute`, {
      duration_minutes: durationMinutes,
    })
  },

  unmuteUser(userId: string): Promise<void> {
    return httpClient.delete(`/api/v1/admin/users/${userId}/mute`)
  },

  verifyUserEmail(userId: string): Promise<User> {
    return httpClient.patch(`/api/v1/admin/users/${userId}/verify-email`)
  },

  // Announcement management
  listAnnouncements(): Promise<AnnouncementRead[]> {
    return httpClient.get('/api/v1/admin/announcements')
  },

  createAnnouncement(payload: {
    title: string
    content: string
    is_published: boolean
    starts_at?: string | null
    ends_at?: string | null
  }): Promise<AnnouncementRead> {
    return httpClient.post('/api/v1/admin/announcements', payload)
  },

  updateAnnouncement(
    id: string,
    payload: {
      title?: string
      content?: string
      is_published?: boolean
      starts_at?: string | null
      ends_at?: string | null
    },
  ): Promise<AnnouncementRead> {
    return httpClient.patch(`/api/v1/admin/announcements/${id}`, payload)
  },

  deleteAnnouncement(id: string): Promise<void> {
    return httpClient.delete(`/api/v1/admin/announcements/${id}`)
  },
}
