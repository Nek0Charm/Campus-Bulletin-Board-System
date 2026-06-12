<template>
  <div class="comment-item" :style="{ marginLeft: depth > 0 ? '24px' : '0' }">
    <div class="comment-main">
      <UserAvatar
        :src="comment.author?.avatar_url"
        :name="comment.author?.nickname || comment.author?.username"
        :size="28"
      />
      <div class="comment-body">
        <div class="comment-header">
          <span class="comment-author">{{
            comment.author?.nickname || comment.author?.username
          }}</span>
          <span v-if="parentAuthorName" class="reply-target">
            回复 <span class="reply-target-name">@{{ parentAuthorName }}</span>
          </span>
          <span class="comment-time">{{ formatTimeAgo(comment.created_at) }}</span>
        </div>
        <div class="comment-content markdown-body" v-html="renderMarkdown(comment.content)" />
        <div class="comment-actions">
          <span class="action-btn" @click="emit('toggle-like', comment.id)">
            <el-icon :size="14" :color="liked ? '#f56c6c' : undefined">
              <ThumbsUp :filled="liked" :size="14" />
            </el-icon>
            {{ comment.like_count }}
          </span>
          <span
            class="action-btn"
            @click="emit('reply', comment.id, comment.author?.nickname || comment.author?.username)"
          >
            <el-icon :size="14"><ChatDotRound /></el-icon> 回复
          </span>
          <span v-if="canDelete" class="action-btn delete-btn" @click="emit('delete', comment.id)">
            <el-icon :size="14"><Delete /></el-icon> 删除
          </span>
        </div>
        <div v-if="comment.replies && comment.replies.length" class="nested-replies">
          <CommentItem
            v-for="child in comment.replies"
            :key="child.id"
            :comment="child"
            :depth="depth + 1"
            :liked-set="likedSet"
            :parent-author-name="replyAuthorMap[child.parent_comment_id ?? '']"
            @reply="(id: string, name: string) => emit('reply', id, name)"
            @toggle-like="(id: string) => emit('toggle-like', id)"
            @delete="(id: string) => emit('delete', id)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChatDotRound, Delete } from '@element-plus/icons-vue'
import ThumbsUp from '@/components/common/ThumbsUp.vue'
import { useAuthStore } from '@/stores/auth'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { renderMarkdown } from '@/utils/markdown'
import '@/styles/markdown.css'
import { formatTimeAgo } from '@/utils/format'
import type { CommentRead } from '@/types/comment'

const props = withDefaults(
  defineProps<{
    comment: CommentRead
    depth?: number
    likedSet?: Set<string>
    parentAuthorName?: string
  }>(),
  {
    depth: 0,
    likedSet: () => new Set(),
    parentAuthorName: undefined,
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

// Build a map of reply id -> author name for all children, so nested replies can show @mention
const replyAuthorMap = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  // Include the root comment itself
  map[props.comment.id] = props.comment.author?.nickname || props.comment.author?.username || ''
  for (const r of props.comment.replies ?? []) {
    map[r.id] = r.author?.nickname || r.author?.username || ''
  }
  return map
})
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

.reply-target {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.reply-target-name {
  color: var(--color-primary);
}

.nested-replies {
  margin-top: var(--spacing-sm);
  padding: 12px;
  background-color: var(--el-fill-color-lighter, #f7f8fa);
  border-radius: 6px;
}

.nested-replies > .comment-item {
  border-bottom: none;
  padding: var(--spacing-xs) 0;
}

.nested-replies > .comment-item:first-child {
  padding-top: 0;
}

.nested-replies > .comment-item:last-child {
  padding-bottom: 0;
}
</style>
