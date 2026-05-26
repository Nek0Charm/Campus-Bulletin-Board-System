export interface Board {
  id: string
  name: string
  slug: string
  description?: string
  sort_order: number
  is_active: boolean
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
  is_active?: boolean
}
