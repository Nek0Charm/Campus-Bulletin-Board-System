import httpClient from './client'
import type { AnnouncementRead } from '@/types/announcement'

export const announcementsAPI = {
  getAnnouncements(): Promise<AnnouncementRead[]> {
    return httpClient.get('/api/v1/announcements/')
  },
}
