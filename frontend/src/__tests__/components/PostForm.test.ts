import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountWithSetup } from '../setup'
import PostForm from '@/components/post/PostForm.vue'

vi.mock('@/api/media', () => ({
  uploadImage: vi.fn<() => void>(),
  getMediaUrl: vi.fn<() => void>(),
  getMediaInfo: vi.fn<() => void>(),
  deleteMedia: vi.fn<() => void>(),
  attachToPost: vi.fn<() => void>(),
  uploadAvatar: vi.fn<() => void>(),
}))

vi.mock('@/api/boards', () => ({
  boardsAPI: {
    getBoards: vi.fn<() => Promise<never[]>>().mockResolvedValue([]),
    getBoard: vi.fn<() => void>(),
    createBoard: vi.fn<() => void>(),
    updateBoard: vi.fn<() => void>(),
    deleteBoard: vi.fn<() => void>(),
    getBoardMasters: vi.fn<() => void>(),
    muteUser: vi.fn<() => void>(),
  },
}))

// Stub the async MdEditor component
const MdEditorStub = {
  template:
    '<textarea class="md-editor-stub" :value="$props.modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" :placeholder="$props.placeholder"></textarea>',
  props: [
    'modelValue',
    'placeholder',
    'toolbarsExclude',
    'markdownItConfig',
    'onUploadImg',
    'style',
  ],
  emits: ['update:modelValue'],
}

describe('PostForm', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function mountForm(props = {}) {
    return mountWithSetup(PostForm, {
      props,
      global: {
        stubs: {
          MdEditor: MdEditorStub,
        },
      },
    })
  }

  it('renders create mode with "发布" button', () => {
    const wrapper = mountForm()
    const buttons = wrapper.findAll('.el-button')
    const submitBtn = buttons.find((b) => b.text() === '发布')
    expect(submitBtn).toBeTruthy()
  })

  it('renders edit mode with "保存修改" button', () => {
    const wrapper = mountForm({ isEdit: true })
    const buttons = wrapper.findAll('.el-button')
    const submitBtn = buttons.find((b) => b.text() === '保存修改')
    expect(submitBtn).toBeTruthy()
  })

  it('pre-fills form fields from initialData', () => {
    const wrapper = mountForm({
      initialData: {
        title: 'Existing Title',
        content: 'Existing Content',
        board_id: 'board-x',
      },
    })

    // Title input
    const titleInput = wrapper
      .findAll('.el-input')
      .find((el) => el.attributes('placeholder') === '请输入帖子标题')
    expect(titleInput?.attributes('value')).toBe('Existing Title')

    // MdEditor textarea
    const editor = wrapper.find('.md-editor-stub')
    expect(editor.attributes('value')).toBe('Existing Content')
  })

  it('emits cancel event', async () => {
    const wrapper = mountForm()
    const buttons = wrapper.findAll('.el-button')
    const cancelBtn = buttons.find((b) => b.text() === '取消')
    expect(cancelBtn).toBeTruthy()

    await cancelBtn!.trigger('click')
    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  it('validates board_id is required', async () => {
    const wrapper = mountForm()

    // Set title via the el-input stub
    const inputs = wrapper.findAll('.el-input')
    const titleInput = inputs.find((el) => el.attributes('placeholder') === '请输入帖子标题')
    await titleInput!.trigger('input')

    // Fill content via MdEditor stub
    const editor = wrapper.find('.md-editor-stub')
    await editor.trigger('input')

    // Submit
    const buttons = wrapper.findAll('.el-button')
    const submitBtn = buttons.find((b) => b.text() === '发布')
    await submitBtn!.trigger('click')

    // No submit emit because validation fails (board_id is still empty)
    expect(wrapper.emitted('submit')).toBeFalsy()
  })

  it('validates title is required', async () => {
    const wrapper = mountForm({
      initialData: { board_id: 'board-x', title: '', content: '' },
    })

    // Fill in content but leave title empty (using initialData above)
    const editor = wrapper.find('.md-editor-stub')
    await editor.trigger('input')

    // Submit
    const buttons = wrapper.findAll('.el-button')
    const submitBtn = buttons.find((b) => b.text() === '发布')
    await submitBtn!.trigger('click')

    // No submit emit
    expect(wrapper.emitted('submit')).toBeFalsy()
  })

  it('validates content is required', async () => {
    const wrapper = mountForm({
      initialData: { board_id: 'board-x', title: 'Title', content: '' },
    })

    // Submit with empty content (already set via initialData)
    const buttons = wrapper.findAll('.el-button')
    const submitBtn = buttons.find((b) => b.text() === '发布')
    await submitBtn!.trigger('click')

    // No submit emit
    expect(wrapper.emitted('submit')).toBeFalsy()
  })

  it('emits submit with trimmed data when all fields are valid', async () => {
    const wrapper = mountForm({
      initialData: { board_id: 'board-x', title: '  My Title  ', content: '  My Content  ' },
    })

    const buttons = wrapper.findAll('.el-button')
    const submitBtn = buttons.find((b) => b.text() === '发布')
    await submitBtn!.trigger('click')

    expect(wrapper.emitted('submit')).toBeTruthy()
    expect(wrapper.emitted('submit')![0]).toEqual([
      {
        title: 'My Title',
        content: 'My Content',
        board_id: 'board-x',
      },
    ])
  })
})
