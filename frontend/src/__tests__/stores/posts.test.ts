import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePostStore } from '@/stores/posts'
import type { PostRead } from '@/types/post'
import type { PaginatedData } from '@/types/api'

vi.mock('@/api/posts', () => ({
  postsAPI: {
    getPosts: vi.fn<() => void>(),
    getPost: vi.fn<() => void>(),
    createPost: vi.fn<() => void>(),
    updatePost: vi.fn<() => void>(),
    deletePost: vi.fn<() => void>(),
    pinPost: vi.fn<() => void>(),
    featurePost: vi.fn<() => void>(),
  },
}))

import { postsAPI } from '@/api/posts'

function makeMockPost(overrides: Partial<PostRead> = {}): PostRead {
  return {
    id: 'post-1',
    title: 'Test Post',
    content: 'Hello world',
    board_id: 'board-1',
    author: {
      id: 'user-1',
      username: 'author',
      nickname: 'Author',
      avatar_url: null,
    },
    is_pinned: false,
    is_featured: false,
    status: 'normal',
    like_count: 0,
    comment_count: 0,
    is_liked: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function makePaginated<T>(items: T[], page = 1, pageSize = 20): PaginatedData<T> {
  return {
    items,
    pagination: {
      page,
      page_size: pageSize,
      total: items.length,
      total_pages: Math.ceil(items.length / pageSize),
    },
  }
}

describe('usePostStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('has correct initial state', () => {
    const store = usePostStore()
    expect(store.postList).toEqual([])
    expect(store.currentPost).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.pagination.total).toBe(0)
    expect(store.pagination.page).toBe(1)
  })

  describe('fetchPosts', () => {
    it('loads posts and updates pagination', async () => {
      const posts = [makeMockPost(), makeMockPost({ id: 'post-2', title: 'Second' })]
      vi.mocked(postsAPI.getPosts).mockResolvedValueOnce(makePaginated(posts))
      const store = usePostStore()

      await store.fetchPosts({ page: 1 })

      expect(postsAPI.getPosts).toHaveBeenCalledWith({
        board_id: undefined,
        page: 1,
        page_size: 20,
      })
      expect(store.postList).toEqual(posts)
      expect(store.pagination.total).toBe(2)
      expect(store.loading).toBe(false)
    })

    it('passes board_id filter', async () => {
      vi.mocked(postsAPI.getPosts).mockResolvedValueOnce(makePaginated([]))
      const store = usePostStore()

      await store.fetchPosts({ board_id: 'board-x' })

      expect(postsAPI.getPosts).toHaveBeenCalledWith({
        board_id: 'board-x',
        page: 1,
        page_size: 20,
      })
    })
  })

  describe('fetchPostById', () => {
    it('sets currentPost', async () => {
      const post = makeMockPost()
      vi.mocked(postsAPI.getPost).mockResolvedValueOnce(post)
      const store = usePostStore()

      await store.fetchPostById('post-1')

      expect(postsAPI.getPost).toHaveBeenCalledWith('post-1')
      expect(store.currentPost).toEqual(post)
      expect(store.loading).toBe(false)
    })
  })

  describe('createPost', () => {
    it('calls API and returns created post', async () => {
      const post = makeMockPost()
      vi.mocked(postsAPI.createPost).mockResolvedValueOnce(post)
      const store = usePostStore()

      const result = await store.createPost({
        title: 'New',
        content: 'Content',
        board_id: 'board-1',
      })

      expect(postsAPI.createPost).toHaveBeenCalledWith({
        title: 'New',
        content: 'Content',
        board_id: 'board-1',
      })
      expect(result).toEqual(post)
    })
  })

  describe('updatePost', () => {
    it('calls API and sets currentPost', async () => {
      const updated = makeMockPost({ title: 'Updated Title' })
      vi.mocked(postsAPI.updatePost).mockResolvedValueOnce(updated)
      const store = usePostStore()

      await store.updatePost('post-1', { title: 'Updated Title' })

      expect(postsAPI.updatePost).toHaveBeenCalledWith('post-1', { title: 'Updated Title' })
      expect(store.currentPost).toEqual(updated)
    })
  })

  describe('deletePost', () => {
    it('removes post from postList and decrements pagination total', async () => {
      vi.mocked(postsAPI.deletePost).mockResolvedValueOnce(undefined as never)
      const store = usePostStore()
      store.$patch({
        postList: [makeMockPost({ id: 'a' }), makeMockPost({ id: 'b' }), makeMockPost({ id: 'c' })],
        pagination: { total: 3, page: 1, pageSize: 20, totalPages: 1 },
      })

      await store.deletePost('b')

      expect(postsAPI.deletePost).toHaveBeenCalledWith('b')
      expect(store.postList).toHaveLength(2)
      expect(store.postList.map((p) => p.id)).toEqual(['a', 'c'])
      expect(store.pagination.total).toBe(2)
    })

    it('clears currentPost if it matches the deleted post', async () => {
      vi.mocked(postsAPI.deletePost).mockResolvedValueOnce(undefined as never)
      const store = usePostStore()
      store.$patch({
        postList: [makeMockPost({ id: 'x' })],
        currentPost: makeMockPost({ id: 'x' }),
        pagination: { total: 1, page: 1, pageSize: 20, totalPages: 0 },
      })

      await store.deletePost('x')

      expect(store.currentPost).toBeNull()
    })

    it('keeps currentPost if it does not match the deleted post', async () => {
      vi.mocked(postsAPI.deletePost).mockResolvedValueOnce(undefined as never)
      const store = usePostStore()
      const other = makeMockPost({ id: 'other' })
      store.$patch({
        postList: [makeMockPost({ id: 'x' }), other],
        currentPost: other,
        pagination: { total: 2, page: 1, pageSize: 20, totalPages: 1 },
      })

      await store.deletePost('x')

      expect(store.currentPost).toEqual(other)
    })

    it('does not decrement total below 0', async () => {
      vi.mocked(postsAPI.deletePost).mockResolvedValueOnce(undefined as never)
      const store = usePostStore()

      await store.deletePost('x')

      expect(store.pagination.total).toBe(0)
    })
  })

  describe('updateLikeCount', () => {
    it('increments like_count on matching post in postList', () => {
      const store = usePostStore()
      const post = makeMockPost({ id: 'p1', like_count: 5 })
      store.$patch({ postList: [post] })

      store.updateLikeCount('p1', 1)

      expect(store.postList[0].like_count).toBe(6)
    })

    it('increments like_count on currentPost when it matches', () => {
      const store = usePostStore()
      const post = makeMockPost({ id: 'p1', like_count: 3 })
      store.$patch({ currentPost: post })

      store.updateLikeCount('p1', 1)

      expect(store.currentPost!.like_count).toBe(4)
    })

    it('clamps like_count to 0', () => {
      const store = usePostStore()
      const post = makeMockPost({ id: 'p1', like_count: 0 })
      store.$patch({ postList: [post] })

      store.updateLikeCount('p1', -1)

      expect(store.postList[0].like_count).toBe(0)
    })

    it('no-ops when post not found', () => {
      const store = usePostStore()
      expect(() => store.updateLikeCount('nonexistent', 1)).not.toThrow()
    })
  })

  describe('updateCommentCount', () => {
    it('increments comment_count on matching post', () => {
      const store = usePostStore()
      const post = makeMockPost({ id: 'p1', comment_count: 10 })
      store.$patch({ postList: [post] })

      store.updateCommentCount('p1', 1)

      expect(store.postList[0].comment_count).toBe(11)
    })

    it('decrements comment_count and clamps to 0', () => {
      const store = usePostStore()
      const post = makeMockPost({ id: 'p1', comment_count: 1 })
      store.$patch({ postList: [post] })

      store.updateCommentCount('p1', -2)

      expect(store.postList[0].comment_count).toBe(0)
    })
  })
})
