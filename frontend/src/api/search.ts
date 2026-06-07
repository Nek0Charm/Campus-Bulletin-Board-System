import httpClient from './client'
import type { PaginatedData } from '@/types/api'
import type { PostRead } from '@/types/post'

export type SearchSort = 'relevance' | 'hot' | 'time'

export interface SearchPostsParams {
  q: string
  board_id?: string
  start_date?: string
  end_date?: string
  sort_by?: SearchSort
  page?: number
  page_size?: number
}

export const searchAPI = {
  searchPosts(params: SearchPostsParams): Promise<PaginatedData<PostRead>> {
    return httpClient.get('/api/v1/search/posts', { params })
  },
}

