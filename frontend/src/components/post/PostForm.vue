<template>
  <div class="post-form">
    <el-form :model="form" label-position="top">
      <el-form-item label="选择板块" required>
        <BoardSelector v-model="form.board_id" />
      </el-form-item>
      <el-form-item label="标题" required>
        <el-input
          v-model="form.title"
          placeholder="请输入帖子标题"
          maxlength="255"
          show-word-limit
        />
      </el-form-item>
      <el-form-item label="内容" required>
        <MdEditor
          v-model="form.content"
          placeholder="请输入帖子内容（支持 Markdown 语法）..."
          :toolbars-exclude="['save', 'htmlPreview', 'pageFullscreen', 'fullscreen']"
          style="min-height: 420px"
        />
      </el-form-item>
    </el-form>
    <div class="form-actions">
      <el-button @click="$emit('cancel')" :disabled="submitting">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        {{ isEdit ? '保存修改' : '发布' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, defineAsyncComponent } from 'vue'
import { ElMessage } from 'element-plus'
import 'md-editor-v3/lib/style.css'
import BoardSelector from '@/components/board/BoardSelector.vue'
import type { PostCreate, PostUpdate } from '@/types/post'
import type { Component } from 'vue'

const MdEditor = defineAsyncComponent(() =>
  import('md-editor-v3').then((m) => m.MdEditor as Component),
)

const props = withDefaults(
  defineProps<{
    initialData?: PostUpdate & { board_id?: string }
    isEdit?: boolean
  }>(),
  {
    isEdit: false,
  },
)

const emit = defineEmits<{
  submit: [data: PostCreate]
  cancel: []
}>()

const form = reactive<PostCreate>({
  title: props.initialData?.title || '',
  content: props.initialData?.content || '',
  board_id: props.initialData?.board_id || '',
})

const submitting = ref(false)

function handleSubmit() {
  if (!form.board_id) {
    ElMessage.warning('请选择板块')
    return
  }
  if (!form.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  if (!form.content.trim()) {
    ElMessage.warning('请输入内容')
    return
  }

  submitting.value = true
  emit('submit', {
    title: form.title.trim(),
    content: form.content.trim(),
    board_id: form.board_id,
  })
  // parent handles: submitting.value = false
}
</script>

<style scoped>
.post-form {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border-light);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}
</style>
