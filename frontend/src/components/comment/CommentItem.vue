<template>
  <div class="comment-item" :style="{ marginLeft: depth > 0 ? '24px' : '0' }">
    <div class="comment-main">
      <UserAvatar :name="comment.author?.nickname || comment.author?.username" :size="28" />
      <div class="comment-body">
        <div class="comment-header">
          <span class="comment-author">{{
            comment.author?.nickname || comment.author?.username
          }}</span>
          <span class="comment-time">{{ formatTimeAgo(comment.created_at) }}</span>
        </div>
        <div class="comment-content">{{ comment.content }}</div>
        <div class="comment-actions">
          <span class="action-btn" @click="emit('toggle-like', comment.id)">
            <el-icon :size="14" :color="liked ? '#f56c6c' : undefined">
              <StarFilled v-if="liked" /><Star v-else />
            </el-icon>
            {{ comment.like_count }}
          </span>
          <span
            v-if="depth === 0"
            class="action-btn"
            @click="emit('reply', comment.id, comment.author?.nickname || comment.author?.username)"
          >
            <el-icon :size="14"><ChatDotRound /></el-icon> 回复
          </span>
          <span v-if="canDelete" class="action-btn delete-btn" @click="emit('delete', comment.id)">
            <el-icon :size="14"><Delete /></el-icon> 删除
          </span>
        </div>
        <template v-if="comment.children && comment.children.length">
          <CommentItem
            v-for="child in comment.children"
            :key="child.id"
            :comment="child"
            :depth="depth + 1"
            :liked-set="likedSet"
            @reply="(id: string, name: string) => emit('reply', id, name)"
            @toggle-like="(id: string) => emit('toggle-like', id)"
            @delete="(id: string) => emit('delete', id)"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Star, StarFilled, ChatDotRound, Delete } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { formatTimeAgo } from '@/utils/format'
import type { CommentRead } from '@/types/comment'

const props = withDefaults(
  defineProps<{
    comment: CommentRead
    depth?: number
    likedSet?: Set<string>
  }>(),
  {
    depth: 0,
    likedSet: () => new Set(),
  },
)

const authStore = useAuthStore()

const emit = defineEmits<{
  reply: [commentId: string, authorName: string]
  'toggle-like': [commentId: string]
  delete: [commentId: string]
}>()

const liked = computed(() => props.likedSet.has(props.comment.id))
const canDelete = computed(
  () => authStore.currentUser?.id === props.comment.author?.id || authStore.isAdmin,
)
</script>

<style scoped>
.comment-item {
  padding: var(--spacing-sm) 0;
}

.comment-item:not(:last-child) {
  border-bottom: 1px solid var(--color-border-light);
}

.comment-main {
  display: flex;
  gap: var(--spacing-sm);
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  margin-bottom: 4px;
}

.comment-author {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.comment-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
}

.comment-content {
  font-size: var(--font-size-base);
  color: var(--color-text-regular);
  line-height: var(--line-height-base);
  margin-bottom: var(--spacing-xs);
  word-break: break-word;
}

.comment-actions {
  display: flex;
  gap: var(--spacing-md);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.action-btn:hover {
  color: var(--color-primary);
}

.delete-btn:hover {
  color: var(--color-danger);
}
</style>
