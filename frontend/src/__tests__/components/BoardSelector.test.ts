import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountWithSetup } from '../setup'
import BoardSelector from '@/components/board/BoardSelector.vue'
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

const mockBoards: Board[] = [
  {
    id: 'board-1',
    name: '课程讨论',
    slug: 'course',
    description: '课程相关',
    sort_order: 1,
    post_count: 5,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'board-2',
    name: '校园生活',
    slug: 'campus',
    description: null as unknown as string,
    sort_order: 2,
    post_count: 0,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

describe('BoardSelector', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches boards on mount', () => {
    vi.mocked(boardsAPI.getBoards).mockResolvedValueOnce(mockBoards)
    useBoardStore()

    mountWithSetup(BoardSelector, {
      props: { modelValue: '' },
    })

    // fetchBoards() is called in onMounted (async, but the call itself is sync)
    expect(boardsAPI.getBoards).toHaveBeenCalledTimes(1)
  })

  it('renders options for each board', () => {
    const store = useBoardStore()
    store.$patch({ boards: mockBoards })

    const wrapper = mountWithSetup(BoardSelector, {
      props: { modelValue: '' },
    })

    const options = wrapper.findAll('.el-option')
    expect(options).toHaveLength(2)
    expect(options[0].text()).toBe('课程讨论')
    expect(options[1].text()).toBe('校园生活')
  })

  it('passes modelValue to el-select', () => {
    const wrapper = mountWithSetup(BoardSelector, {
      props: { modelValue: 'board-1' },
    })

    const select = wrapper.find('.el-select')
    expect(select.attributes('value')).toBe('board-1')
  })

  it('emits update:modelValue when selection changes', async () => {
    const wrapper = mountWithSetup(BoardSelector, {
      props: { modelValue: '' },
    })

    const select = wrapper.find('.el-select')
    await select.trigger('change')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('renders when board store is empty', () => {
    const wrapper = mountWithSetup(BoardSelector, {
      props: { modelValue: '' },
    })

    expect(wrapper.find('.el-select').exists()).toBe(true)
    expect(wrapper.findAll('.el-option')).toHaveLength(0)
  })
})
