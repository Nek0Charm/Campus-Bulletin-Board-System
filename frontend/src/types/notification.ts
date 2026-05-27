export type NotificationType = 'comment' | 'reply' | 'like' | 'system'

export interface NotificationRead {
  id: string
  recipient_id: string
  actor?: {
    id: string
    username: string
    nickname?: string
    avatar_url?: string
  }
  type: NotificationType
  title: string
  content: string
  related_type?: string
  related_id?: string
  is_read: boolean
  read_at?: string
  created_at: string
}
