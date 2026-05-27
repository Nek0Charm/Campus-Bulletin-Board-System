export type PostStatus = 'normal' | 'hidden' | 'deleted'

export interface PostRead {
  id: string
  title: string
  content?: string
  board_id: string
  author: {
    id: string
    username: string
    nickname?: string
    avatar_url?: string
  }
  is_pinned: boolean
  is_featured: boolean
  status: PostStatus
  like_count: number
  comment_count: number
  view_count: number
  published_at?: string
  created_at: string
  updated_at: string
}

export interface PostCreate {
  title: string
  content: string
  board_id: string
}

export interface PostUpdate {
  title?: string
  content?: string
  board_id?: string
}
