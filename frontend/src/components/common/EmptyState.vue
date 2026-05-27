<template>
  <div class="empty-state">
    <el-icon :size="48" color="#c0c4cc"><FolderOpened /></el-icon>
    <p class="empty-title">{{ title }}</p>
    <p v-if="description" class="empty-desc">{{ description }}</p>
    <el-button v-if="actionText" type="primary" @click="$emit('action')">
      {{ actionText }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { FolderOpened } from '@element-plus/icons-vue'

withDefaults(
  defineProps<{
    title?: string
    description?: string
    actionText?: string
  }>(),
  {
    title: '暂无数据',
  },
)

defineEmits<{ action: [] }>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl) var(--spacing-md);
  text-align: center;
}

.empty-title {
  margin-top: var(--spacing-md);
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
}

.empty-desc {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-placeholder);
}

.el-button {
  margin-top: var(--spacing-md);
}
</style>
