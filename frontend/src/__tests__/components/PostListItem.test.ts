import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mountWithSetup } from '../setup'
import PostListItem from '@/components/post/PostListItem.vue'
import type { PostRead } from '@/types/post'

vi.mock('@/utils/format', () => ({
  formatTimeAgo: vi.fn<(_date: string) => string>(() => '3小时前'),
}))

vi.mock('@/utils/markdown', () => ({
  stripMarkdown: vi.fn<(content: string) => string>((content: string) => content),
  renderMarkdown: vi.fn<() => void>(),
}))

import { stripMarkdown } from '@/utils/markdown'

function makeMockPost(overrides: Partial<PostRead> = {}): PostRead {
  return {
    id: 'post-1',
    title: 'Test Post Title',
    content: 'This is some **markdown** content that is quite long for testing purposes.',
    board_id: 'board-1',
    author: {
      id: 'user-1',
      username: 'testauthor',
      nickname: 'Test Author',
      avatar_url: undefined,
    },
    is_pinned: false,
    is_featured: false,
    status: 'normal',
    like_count: 5,
    comment_count: 3,
    is_liked: false,
    published_at: '2026-01-01T00:00:00Z',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('PostListItem', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders post title', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost() },
    })
    expect(wrapper.find('.post-title').text()).toBe('Test Post Title')
  })

  it('renders author nickname', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost() },
    })
    expect(wrapper.find('.meta-author').text()).toBe('Test Author')
  })

  it('falls back to username when nickname is not set', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: {
        post: makeMockPost({
          author: { id: 'u1', username: 'no_nick', nickname: undefined, avatar_url: undefined },
        }),
      },
    })
    expect(wrapper.find('.meta-author').text()).toBe('no_nick')
  })

  it('renders time via formatTimeAgo', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost() },
    })
    expect(wrapper.find('.meta-time').text()).toBe('3小时前')
  })

  it('renders like and comment counts', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ like_count: 10, comment_count: 7 }) },
    })
    const stats = wrapper.find('.post-stats')
    expect(stats.text()).toContain('10')
    expect(stats.text()).toContain('7')
  })

  it('renders markdown-stripped preview', () => {
    vi.mocked(stripMarkdown).mockReturnValue('Plain text preview')
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ content: '**bold** and more' }) },
    })
    expect(stripMarkdown).toHaveBeenCalledWith('**bold** and more')
    expect(wrapper.find('.post-preview').text()).toBe('Plain text preview')
  })

  it('truncates preview longer than 120 characters', () => {
    const longText = 'a'.repeat(200)
    vi.mocked(stripMarkdown).mockReturnValue(longText)
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ content: longText }) },
    })
    const preview = wrapper.find('.post-preview').text()
    expect(preview.length).toBe(123) // 120 + '...'
    expect(preview.endsWith('...')).toBe(true)
  })

  it('does not truncate short content', () => {
    const shortText = 'Short text'
    vi.mocked(stripMarkdown).mockReturnValue(shortText)
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ content: shortText }) },
    })
    expect(wrapper.find('.post-preview').text()).toBe('Short text')
  })

  it('emits click event with post id when clicked', async () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ id: 'my-post-id' }) },
    })
    await wrapper.find('.post-list-item').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')![0]).toEqual(['my-post-id'])
  })

  it('renders PostStatusTag when post is pinned', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ is_pinned: true }) },
    })
    // PostStatusTag is rendered as a stubbed component
    expect(wrapper.findComponent({ name: 'PostStatusTag' }).exists()).toBe(true)
  })

  it('renders PostStatusTag when post is featured', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ is_featured: true }) },
    })
    expect(wrapper.findComponent({ name: 'PostStatusTag' }).exists()).toBe(true)
  })

  it('does not render PostStatusTag when neither pinned nor featured', () => {
    const wrapper = mountWithSetup(PostListItem, {
      props: { post: makeMockPost({ is_pinned: false, is_featured: false }) },
    })
    expect(wrapper.findComponent({ name: 'PostStatusTag' }).exists()).toBe(false)
  })
})
