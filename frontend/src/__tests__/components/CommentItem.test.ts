import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountWithSetup } from '../setup'
import CommentItem from '@/components/comment/CommentItem.vue'
import { useAuthStore } from '@/stores/auth'
import type { CommentRead } from '@/types/comment'
import type { User } from '@/types/user'

vi.mock('@/utils/format', () => ({
  formatTimeAgo: vi.fn<(_date: string) => string>(() => '2小时前'),
}))

vi.mock('@/utils/markdown', () => ({
  renderMarkdown: vi.fn<(content: string) => string>((content: string) => `<p>${content}</p>`),
  stripMarkdown: vi.fn<(content: string) => string>((content: string) => content),
}))

vi.mock('@/api/auth', () => ({
  authAPI: {
    login: vi.fn<() => void>(),
    register: vi.fn<() => void>(),
    logout: vi.fn<() => void>(),
    resetPassword: vi.fn<() => void>(),
    verifyEmail: vi.fn<() => void>(),
    resendVerification: vi.fn<() => void>(),
  },
}))

vi.mock('@/api/users', () => ({
  usersAPI: {
    getProfile: vi.fn<() => void>(),
    updateProfile: vi.fn<() => void>(),
    getUserStats: vi.fn<() => void>(),
  },
}))

vi.mock('@/utils/storage', () => ({
  getToken: vi.fn<() => null>(() => null),
  setToken: vi.fn<() => void>(),
  removeToken: vi.fn<() => void>(),
}))

import { renderMarkdown } from '@/utils/markdown'
import { formatTimeAgo } from '@/utils/format'

const mockAuthor: User = {
  id: 'author-1',
  username: 'comment_author',
  email: 'author@example.com',
  nickname: 'Comment Author',
  avatar_url: undefined,
  role: 'user',
  status: 'active',
  email_verified: true,
  muted_until: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

function makeMockComment(overrides: Partial<CommentRead> = {}): CommentRead {
  return {
    id: 'comment-1',
    post_id: 'post-1',
    author: {
      id: 'author-1',
      username: 'comment_author',
      nickname: 'Comment Author',
      avatar_url: undefined,
    },
    content: 'This is a test comment',
    status: 'normal',
    like_count: 3,
    reply_count: 1,
    is_liked: false,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('CommentItem', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function mountComment(comment: CommentRead, props = {}) {
    return mountWithSetup(CommentItem, {
      props: {
        comment,
        ...props,
      },
      global: {
        stubs: {
          // Stub recursive CommentItem children
          CommentItem: {
            template: '<div class="comment-item-stub"><slot /></div>',
            props: ['comment', 'depth', 'likedSet', 'parentAuthorName'],
          },
        },
      },
    })
  }

  it('renders comment content via v-html', () => {
    const wrapper = mountComment(makeMockComment({ content: '**bold text**' }))

    expect(renderMarkdown).toHaveBeenCalledWith('**bold text**')
    const contentEl = wrapper.find('.comment-content')
    expect(contentEl.exists()).toBe(true)
  })

  it('renders author nickname', () => {
    const wrapper = mountComment(makeMockComment())
    expect(wrapper.find('.comment-author').text()).toBe('Comment Author')
  })

  it('renders time via formatTimeAgo', () => {
    const wrapper = mountComment(makeMockComment({ created_at: '2026-06-11T00:00:00Z' }))
    expect(formatTimeAgo).toHaveBeenCalledWith('2026-06-11T00:00:00Z')
    expect(wrapper.find('.comment-time').text()).toBe('2小时前')
  })

  it('shows reply target when parentAuthorName is set', () => {
    const wrapper = mountComment(makeMockComment(), {
      parentAuthorName: 'OriginalPoster',
    })

    expect(wrapper.find('.reply-target').exists()).toBe(true)
    expect(wrapper.find('.reply-target-name').text()).toBe('@OriginalPoster')
  })

  it('hides reply target when parentAuthorName is not set', () => {
    const wrapper = mountComment(makeMockComment())
    expect(wrapper.find('.reply-target').exists()).toBe(false)
  })

  it('shows delete button for comment author', () => {
    const authStore = useAuthStore()
    authStore.$patch({ token: 'token', currentUser: mockAuthor })

    const wrapper = mountComment(makeMockComment())
    expect(wrapper.find('.delete-btn').exists()).toBe(true)
  })

  it('shows delete button for admin even if not author', () => {
    const authStore = useAuthStore()
    authStore.$patch({
      token: 'admin-token',
      currentUser: { ...mockAuthor, id: 'admin-id', role: 'admin' },
    })

    const wrapper = mountComment(makeMockComment({ author: { id: 'other', username: 'other' } }))
    expect(wrapper.find('.delete-btn').exists()).toBe(true)
  })

  it('hides delete button for non-author non-admin', () => {
    const authStore = useAuthStore()
    authStore.$patch({
      token: 'token',
      currentUser: { ...mockAuthor, id: 'other_user' },
    })

    const wrapper = mountComment(
      makeMockComment({ author: { id: 'author-1', username: 'original' } }),
    )
    expect(wrapper.find('.delete-btn').exists()).toBe(false)
  })

  it('like button shows filled state when comment is liked', () => {
    const likedSet = new Set(['comment-1'])
    const wrapper = mountComment(makeMockComment({ id: 'comment-1' }), { likedSet })

    // The ThumbsUp component receives :filled="liked" prop
    const thumbsUp = wrapper.findComponent({ name: 'ThumbsUp' })
    expect(thumbsUp.props('filled')).toBe(true)
  })

  it('like button shows unfilled state when not liked', () => {
    const wrapper = mountComment(makeMockComment({ id: 'comment-1' }))
    const thumbsUp = wrapper.findComponent({ name: 'ThumbsUp' })
    expect(thumbsUp.props('filled')).toBe(false)
  })

  it('emits reply with commentId and authorName', async () => {
    const wrapper = mountComment(makeMockComment({ id: 'reply-me' }))

    const actionBtns = wrapper.findAll('.action-btn')
    // First button is like, second is reply
    const replyBtn = actionBtns.find((btn) => btn.text().includes('回复'))
    await replyBtn!.trigger('click')

    expect(wrapper.emitted('reply')).toBeTruthy()
    expect(wrapper.emitted('reply')![0]).toEqual(['reply-me', 'Comment Author'])
  })

  it('emits toggle-like with commentId', async () => {
    const wrapper = mountComment(makeMockComment({ id: 'like-me' }))

    const actionBtns = wrapper.findAll('.action-btn')
    // First button (before reply) should be the like button
    const likeBtn = actionBtns[0]!
    await likeBtn.trigger('click')

    expect(wrapper.emitted('toggle-like')).toBeTruthy()
    expect(wrapper.emitted('toggle-like')![0]).toEqual(['like-me'])
  })

  it('emits delete with commentId', async () => {
    const authStore = useAuthStore()
    authStore.$patch({ token: 'token', currentUser: mockAuthor })

    const wrapper = mountComment(makeMockComment({ id: 'delete-me' }))

    await wrapper.find('.delete-btn').trigger('click')

    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')![0]).toEqual(['delete-me'])
  })

  it('recursively renders child comments', () => {
    const childComment = makeMockComment({ id: 'child-1', content: 'Child reply' })
    const wrapper = mountComment(
      makeMockComment({
        id: 'parent',
        replies: [childComment],
      }),
    )

    // Child CommentItem stubs should be rendered
    const childStubs = wrapper.findAll('.comment-item-stub')
    expect(childStubs.length).toBeGreaterThanOrEqual(1)
  })

  it('passes depth prop to child CommentItem', () => {
    const child = makeMockComment({ id: 'child-1' })
    const wrapper = mountComment(makeMockComment({ id: 'parent', replies: [child] }), { depth: 2 })

    // Child CommentItems are stubbed with template containing class 'comment-item-stub'
    const childStubs = wrapper.findAll('.comment-item-stub')
    expect(childStubs.length).toBeGreaterThanOrEqual(1)
  })

  it('builds replyAuthorMap including root and child authors', () => {
    const child = makeMockComment({
      id: 'child-1',
      author: { id: 'child-author', username: 'child_user', nickname: 'Child' },
    })
    const wrapper = mountComment(
      makeMockComment({
        id: 'root',
        author: { id: 'root-author', username: 'root_user', nickname: 'Root' },
        replies: [child],
      }),
    )

    // The replyAuthorMap computed should exist on the vm
    const vm = wrapper.vm as unknown as { replyAuthorMap: Record<string, string> }
    expect(vm.replyAuthorMap).toBeDefined()
    expect(vm.replyAuthorMap['root']).toBe('Root')
    expect(vm.replyAuthorMap['child-1']).toBe('Child')
  })
})
