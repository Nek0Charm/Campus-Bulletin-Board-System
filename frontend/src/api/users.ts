import httpClient from './client'
import type { User } from '@/types/user'

export interface UserStats {
  post_count: number
  comment_count: number
  like_count: number
}

export const usersAPI = {
  getProfile(): Promise<User> {
    return httpClient.get('/api/v1/users/me')
  },

  updateProfile(payload: { nickname?: string; avatar_url?: string }): Promise<User> {
    return httpClient.patch('/api/v1/users/me', payload)
  },

  getUserStats(): Promise<UserStats> {
    return httpClient.get('/api/v1/users/me/stats')
  },
}
