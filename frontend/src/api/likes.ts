import httpClient from './client'

export const likesAPI = {
  likePost(postId: string): Promise<void> {
    return httpClient.post(`/api/v1/likes/posts/${postId}`)
  },

  unlikePost(postId: string): Promise<void> {
    return httpClient.delete(`/api/v1/likes/posts/${postId}`)
  },

  likeComment(commentId: string): Promise<void> {
    return httpClient.post(`/api/v1/likes/comments/${commentId}`)
  },

  unlikeComment(commentId: string): Promise<void> {
    return httpClient.delete(`/api/v1/likes/comments/${commentId}`)
  },
}
