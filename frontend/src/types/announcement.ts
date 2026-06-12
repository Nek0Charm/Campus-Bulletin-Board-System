export interface AnnouncementRead {
  id: string
  title: string
  content: string
  is_published: boolean
  starts_at: string | null
  ends_at: string | null
  created_by: string
  created_at: string
  updated_at: string
}
