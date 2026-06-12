<template>
  <div class="board-card" @click="$emit('click', board)">
    <div class="board-icon">
      <el-icon :size="28"><component :is="iconComponent" /></el-icon>
    </div>
    <div class="board-info">
      <h3 class="board-name">{{ board.name }}</h3>
      <p class="board-desc">{{ board.description || '暂无描述' }}</p>
      <span class="board-count">{{ board.post_count ?? 0 }} 篇帖子</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Reading, UserFilled, HomeFilled } from '@element-plus/icons-vue'
import type { Board } from '@/types/board'

const props = defineProps<{ board: Board }>()
defineEmits<{ click: [board: Board] }>()

const iconComponent = computed(() => {
  const name = props.board.slug
  if (name.includes('course') || name.includes('academic')) return Reading
  if (name.includes('club') || name.includes('job')) return UserFilled
  return HomeFilled
})
</script>

<style scoped>
.board-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition:
    background var(--transition-fast),
    border-color var(--transition-fast);
}

.board-card:hover {
  background-color: #fafbfc;
  border-color: var(--color-primary-light);
}

.board-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: #fff;
  flex-shrink: 0;
}

.board-info {
  flex: 1;
  min-width: 0;
  text-align: left;
}

.board-name {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.board-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.board-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
}
</style>
