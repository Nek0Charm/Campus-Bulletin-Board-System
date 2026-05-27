import httpClient from './client'

export const likesAPI = {
  likePost(postId: string): Promise<void> {
    return httpClient.post(`/api/v1/posts/${postId}/like`)
  },

  unlikePost(postId: string): Promise<void> {
    return httpClient.delete(`/api/v1/posts/${postId}/like`)
  },

  likeComment(commentId: string): Promise<void> {
    return httpClient.post(`/api/v1/comments/${commentId}/like`)
  },

  unlikeComment(commentId: string): Promise<void> {
    return httpClient.delete(`/api/v1/comments/${commentId}/like`)
  },
}
