import { describe, it, expect } from 'vitest'
import { mountWithSetup } from '../setup'
import EmptyState from '@/components/common/EmptyState.vue'

describe('EmptyState', () => {
  it('renders default title', () => {
    const wrapper = mountWithSetup(EmptyState)
    expect(wrapper.find('.empty-title').text()).toBe('暂无数据')
  })

  it('renders custom title', () => {
    const wrapper = mountWithSetup(EmptyState, {
      props: { title: '没有帖子' },
    })
    expect(wrapper.find('.empty-title').text()).toBe('没有帖子')
  })

  it('renders description when provided', () => {
    const wrapper = mountWithSetup(EmptyState, {
      props: { description: '这里还没有任何内容' },
    })
    expect(wrapper.find('.empty-desc').exists()).toBe(true)
    expect(wrapper.find('.empty-desc').text()).toBe('这里还没有任何内容')
  })

  it('omits description element when not provided', () => {
    const wrapper = mountWithSetup(EmptyState)
    expect(wrapper.find('.empty-desc').exists()).toBe(false)
  })

  it('renders action button when actionText is provided', () => {
    const wrapper = mountWithSetup(EmptyState, {
      props: { actionText: '去发帖' },
    })
    const btn = wrapper.find('.el-button')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toBe('去发帖')
  })

  it('omits action button when actionText is not provided', () => {
    const wrapper = mountWithSetup(EmptyState)
    expect(wrapper.find('.el-button').exists()).toBe(false)
  })

  it('emits action when button is clicked', async () => {
    const wrapper = mountWithSetup(EmptyState, {
      props: { actionText: '去发帖' },
    })
    await wrapper.find('.el-button').trigger('click')
    expect(wrapper.emitted('action')).toBeTruthy()
  })
})
