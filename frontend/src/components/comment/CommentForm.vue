<template>
  <div class="comment-form">
    <p v-if="replyTo" class="reply-hint">
      回复 <strong>{{ replyTo }}</strong>
      <el-button type="primary" link size="small" @click="$emit('cancel')">取消</el-button>
    </p>
    <div class="input-row">
      <el-input
        v-model="content"
        :placeholder="replyTo ? `回复 ${replyTo}...` : '发表评论...'"
        :rows="2"
        type="textarea"
        @keydown.enter.exact.prevent="handleSubmit"
      />
    </div>
    <div class="form-actions">
      <el-button type="primary" size="small" :loading="submitting" @click="handleSubmit">
        发表评论
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  replyTo?: string
  onSubmit?: (content: string) => Promise<void>
}>()

defineEmits<{
  cancel: []
}>()

const content = ref('')
const submitting = ref(false)

async function handleSubmit() {
  const text = content.value.trim()
  if (!text) {
    ElMessage.warning('请输入评论内容')
    return
  }
  if (submitting.value || !props.onSubmit) return

  submitting.value = true
  try {
    await props.onSubmit(text)
    content.value = ''
  } catch {
    // keep content for retry
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.comment-form {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  padding: var(--spacing-md);
}

.reply-hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.input-row {
  margin-bottom: var(--spacing-sm);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
