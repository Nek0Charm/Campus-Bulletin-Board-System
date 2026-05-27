import httpClient from './client'
import type { User } from '@/types/user'
import type { PaginatedData } from '@/types/api'

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
}
