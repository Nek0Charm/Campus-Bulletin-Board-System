export interface Board {
  id: string
  name: string
  slug: string
  description?: string
  sort_order: number
  post_count?: number
  created_at: string
}

export interface BoardCreate {
  name: string
  slug: string
  description?: string
  sort_order?: number
}

export interface BoardUpdate {
  name?: string
  slug?: string
  description?: string
  sort_order?: number
}

export interface BoardMasterUserInfo {
  id: string
  username: string
  nickname?: string
  avatar_url?: string
}

export interface BoardMasterInfo {
  id: string
  board_id: string
  user_id: string
  user: BoardMasterUserInfo
  created_at: string
}
