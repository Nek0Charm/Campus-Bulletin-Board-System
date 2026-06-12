import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mountWithSetup } from '../setup'
import type { VueWrapper } from '@vue/test-utils'
import PaginationBar from '@/components/common/PaginationBar.vue'

describe('PaginationBar', () => {
  beforeEach(() => {
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  })

  it('renders pagination with correct total', () => {
    const wrapper = mountWithSetup(PaginationBar, {
      props: {
        currentPage: 1,
        pageSize: 20,
        total: 100,
      },
    })
    const el = wrapper.find('.el-pagination')
    expect(el.attributes('data-total')).toBe('100')
  })

  it('renders with custom page size options', () => {
    const wrapper = mountWithSetup(PaginationBar, {
      props: {
        currentPage: 1,
        pageSize: 10,
        total: 50,
        pageSizeOptions: [10, 25, 50],
      },
    })
    expect(wrapper.find('.el-pagination').exists()).toBe(true)
  })

  it('emits page-change and scrolls to top on page change', async () => {
    const wrapper = mountWithSetup(PaginationBar, {
      props: {
        currentPage: 1,
        pageSize: 20,
        total: 100,
      },
    })

    // Simulate the el-pagination emitting update:currentPage
    const paginationStub = wrapper.findComponent('.el-pagination') as VueWrapper
    await paginationStub.vm.$emit('update:currentPage', 3)

    expect(wrapper.emitted('page-change')).toBeTruthy()
    expect(wrapper.emitted('page-change')![0]).toEqual([3])
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
  })

  it('emits size-change on page size change', async () => {
    const wrapper = mountWithSetup(PaginationBar, {
      props: {
        currentPage: 1,
        pageSize: 20,
        total: 100,
      },
    })

    const paginationStub2 = wrapper.findComponent('.el-pagination') as VueWrapper
    await paginationStub2.vm.$emit('update:pageSize', 50)

    expect(wrapper.emitted('size-change')).toBeTruthy()
    expect(wrapper.emitted('size-change')![0]).toEqual([50])
  })
})
