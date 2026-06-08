import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { postsAPI } from '@/api/posts'
import type { PostRead } from '@/types/post'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'

export const usePostStore = defineStore('posts', () => {
  const postList = ref<PostRead[]>([])
  const currentPost = ref<PostRead | null>(null)
  const loading = ref(false)
  const pagination = reactive({
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
    total: 0,
    totalPages: 0,
  })

  async function fetchPosts(params: { board_id?: string; page?: number; page_size?: number }) {
    loading.value = true
    try {
      const data = await postsAPI.getPosts({
        board_id: params.board_id,
        page: params.page || 1,
        page_size: params.page_size || DEFAULT_PAGE_SIZE,
      })
      postList.value = data.items
      Object.assign(pagination, data.pagination)
    } finally {
      loading.value = false
    }
  }

  async function fetchPostById(id: string) {
    loading.value = true
    try {
      currentPost.value = await postsAPI.getPost(id)
    } finally {
      loading.value = false
    }
  }

  async function createPost(payload: {
    title: string
    content: string
    board_id: string
  }): Promise<PostRead> {
    return postsAPI.createPost(payload)
  }

  async function updatePost(
    id: string,
    payload: { title?: string; content?: string; board_id?: string },
  ) {
    currentPost.value = await postsAPI.updatePost(id, payload)
  }

  async function deletePost(id: string) {
    await postsAPI.deletePost(id)
    postList.value = postList.value.filter((p) => p.id !== id)
    if (pagination.total > 0) pagination.total--
    if (currentPost.value?.id === id) currentPost.value = null
  }

  function updateLikeCount(postId: string, delta: number) {
    const post = postList.value.find((p) => p.id === postId)
    if (post) post.like_count = Math.max(0, post.like_count + delta)
    if (currentPost.value?.id === postId) {
      currentPost.value.like_count = Math.max(0, currentPost.value.like_count + delta)
    }
  }

  function updateCommentCount(postId: string, delta: number) {
    const post = postList.value.find((p) => p.id === postId)
    if (post) post.comment_count = Math.max(0, post.comment_count + delta)
    if (currentPost.value?.id === postId) {
      currentPost.value.comment_count = Math.max(0, currentPost.value.comment_count + delta)
    }
  }

  return {
    postList,
    currentPost,
    loading,
    pagination,
    fetchPosts,
    fetchPostById,
    createPost,
    updatePost,
    deletePost,
    updateLikeCount,
    updateCommentCount,
  }
})
