import httpClient from './client'

export interface PostLikeStatus {
  is_liked: boolean
  liked_comment_ids: string[]
}

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

  getMyLikeStatus(postId: string): Promise<PostLikeStatus> {
    return httpClient.get('/api/v1/likes/my-status', { params: { post_id: postId } })
  },
}
