import httpClient from './client'
import type { CommentRead, CommentCreate } from '@/types/comment'
import type { PaginatedData } from '@/types/api'

export const commentsAPI = {
  getComments(
    postId: string,
    params?: { page?: number; page_size?: number },
  ): Promise<PaginatedData<CommentRead>> {
    return httpClient.get(`/api/v1/posts/${postId}/comments`, { params })
  },

  createComment(postId: string, payload: CommentCreate): Promise<CommentRead> {
    return httpClient.post(`/api/v1/posts/${postId}/comments`, payload)
  },

  deleteComment(commentId: string): Promise<void> {
    return httpClient.delete(`/api/v1/comments/${commentId}`)
  },
}
