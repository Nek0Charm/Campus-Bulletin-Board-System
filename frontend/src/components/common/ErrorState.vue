<template>
  <div class="error-state">
    <el-icon :size="48" color="#f56c6c"><WarningFilled /></el-icon>
    <p class="error-msg">{{ message }}</p>
    <el-button v-if="showRetry" type="primary" @click="$emit('retry')">
      {{ retryText }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { WarningFilled } from '@element-plus/icons-vue'

withDefaults(
  defineProps<{
    message?: string
    showRetry?: boolean
    retryText?: string
  }>(),
  {
    message: '加载失败，请稍后重试',
    showRetry: true,
    retryText: '重试',
  },
)

defineEmits<{ retry: [] }>()
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl) var(--spacing-md);
  text-align: center;
}

.error-msg {
  margin-top: var(--spacing-md);
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
}

.el-button {
  margin-top: var(--spacing-md);
}
</style>
