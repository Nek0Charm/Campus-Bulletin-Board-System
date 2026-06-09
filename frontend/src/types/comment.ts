export type CommentStatus = 'normal' | 'hidden' | 'deleted'

export interface CommentRead {
  id: string
  post_id: string
  author: {
    id: string
    username: string
    nickname?: string
    avatar_url?: string
  }
  parent_comment_id?: string | null
  root_comment_id?: string | null
  content: string
  status: CommentStatus
  like_count: number
  reply_count: number
  is_liked?: boolean
  created_at: string
  replies?: CommentRead[]
}

export interface CommentCreate {
  content: string
  parent_comment_id?: string | null
}
