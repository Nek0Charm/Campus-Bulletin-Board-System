import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBoardStore } from '@/stores/boards'
import type { Board } from '@/types/board'

vi.mock('@/api/boards', () => ({
  boardsAPI: {
    getBoards: vi.fn<() => void>(),
    getBoard: vi.fn<() => void>(),
    createBoard: vi.fn<() => void>(),
    updateBoard: vi.fn<() => void>(),
    deleteBoard: vi.fn<() => void>(),
    getBoardMasters: vi.fn<() => void>(),
    muteUser: vi.fn<() => void>(),
  },
}))

import { boardsAPI } from '@/api/boards'

const mockBoard: Board = {
  id: 'board-1',
  name: '课程讨论',
  slug: 'course-discussion',
  description: '课程相关讨论',
  sort_order: 1,
  post_count: 3,
  created_at: '2026-01-01T00:00:00Z',
}

const mockBoards: Board[] = [
  mockBoard,
  {
    id: 'board-2',
    name: '校园生活',
    slug: 'campus-life',
    description: undefined,
    sort_order: 2,
    post_count: 0,
    created_at: '2026-01-01T00:00:00Z',
  },
]

describe('useBoardStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('has correct initial state', () => {
    const store = useBoardStore()
    expect(store.boards).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchBoards() loads boards from API', async () => {
    vi.mocked(boardsAPI.getBoards).mockResolvedValueOnce(mockBoards)
    const store = useBoardStore()

    await store.fetchBoards()

    expect(boardsAPI.getBoards).toHaveBeenCalledOnce()
    expect(store.boards).toEqual(mockBoards)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchBoards() skips API call when boards are already loaded', async () => {
    vi.mocked(boardsAPI.getBoards).mockResolvedValueOnce(mockBoards)
    const store = useBoardStore()

    await store.fetchBoards()
    await store.fetchBoards()

    expect(boardsAPI.getBoards).toHaveBeenCalledTimes(1)
  })

  it('fetchBoards(true) forces reload even when cached', async () => {
    vi.mocked(boardsAPI.getBoards).mockResolvedValue(mockBoards)
    const store = useBoardStore()

    await store.fetchBoards()
    await store.fetchBoards(true)

    expect(boardsAPI.getBoards).toHaveBeenCalledTimes(2)
  })

  it('fetchBoards() sets error string on API failure', async () => {
    vi.mocked(boardsAPI.getBoards).mockRejectedValueOnce(new Error('Network error'))
    const store = useBoardStore()

    await store.fetchBoards()

    expect(store.error).toBe('加载板块失败')
    expect(store.loading).toBe(false)
    expect(store.boards).toEqual([])
  })

  it('fetchBoards() clears previous error on retry', async () => {
    vi.mocked(boardsAPI.getBoards).mockRejectedValueOnce(new Error('fail'))
    const store = useBoardStore()
    await store.fetchBoards()
    expect(store.error).toBe('加载板块失败')

    vi.mocked(boardsAPI.getBoards).mockResolvedValueOnce(mockBoards)
    await store.fetchBoards(true)
    expect(store.error).toBeNull()
    expect(store.boards).toEqual(mockBoards)
  })
})
