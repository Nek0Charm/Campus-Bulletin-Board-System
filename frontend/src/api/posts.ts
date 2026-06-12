import httpClient from './client'
import type { PostRead, PostCreate, PostUpdate } from '@/types/post'
import type { PaginatedData } from '@/types/api'

export const postsAPI = {
  getPosts(params: {
    board_id?: string
    author_id?: string
    page?: number
    page_size?: number
    sort_by?: string
    is_featured?: boolean
  }): Promise<PaginatedData<PostRead>> {
    return httpClient.get('/api/v1/posts/', { params })
  },

  getPost(id: string): Promise<PostRead> {
    return httpClient.get(`/api/v1/posts/${id}`)
  },

  createPost(payload: PostCreate): Promise<PostRead> {
    return httpClient.post('/api/v1/posts/', payload)
  },

  updatePost(id: string, payload: PostUpdate): Promise<PostRead> {
    return httpClient.patch(`/api/v1/posts/${id}`, payload)
  },

  deletePost(id: string): Promise<void> {
    return httpClient.delete(`/api/v1/posts/${id}`)
  },

  pinPost(id: string, is_pinned: boolean): Promise<PostRead> {
    return httpClient.patch(`/api/v1/posts/${id}/pin`, { is_pinned })
  },

  featurePost(id: string, is_featured: boolean): Promise<PostRead> {
    return httpClient.patch(`/api/v1/posts/${id}/feature`, { is_featured })
  },
}
