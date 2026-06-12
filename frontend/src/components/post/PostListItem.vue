<template>
  <div class="post-list-item" @click="$emit('click', post.id)">
    <div class="post-main">
      <div class="post-title-row">
        <PostStatusTag
          v-if="post.is_pinned || post.is_featured"
          :is-pinned="post.is_pinned"
          :is-featured="post.is_featured"
        />
        <h3 class="post-title">{{ post.title }}</h3>
      </div>
      <div class="post-meta">
        <UserAvatar
          :src="post.author?.avatar_url"
          :name="post.author?.nickname || post.author?.username"
          :size="18"
        />
        <span class="meta-author">{{ post.author?.nickname || post.author?.username }}</span>
        <span class="meta-time">{{ formatTimeAgo(post.created_at) }}</span>
      </div>
      <div class="post-preview" v-if="post.content">
        {{ preview }}
      </div>
    </div>
    <div class="post-stats">
      <span class="stat-item">
        <el-icon :size="14"><ThumbsUp /></el-icon>
        {{ post.like_count }}
      </span>
      <span class="stat-item">
        <el-icon :size="14"><ChatDotRound /></el-icon>
        {{ post.comment_count }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import ThumbsUp from '@/components/common/ThumbsUp.vue'
import PostStatusTag from './PostStatusTag.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { formatTimeAgo } from '@/utils/format'
import { stripMarkdown } from '@/utils/markdown'
import type { PostRead } from '@/types/post'

const props = defineProps<{ post: PostRead }>()
defineEmits<{ click: [postId: string] }>()

const preview = computed(() => {
  const text = stripMarkdown(props.post.content ?? '')
  return text.length > 120 ? text.substring(0, 120) + '...' : text
})
</script>

<style scoped>
.post-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  cursor: pointer;
  transition: background var(--transition-fast);
  border-bottom: 1px solid var(--color-border-list);
}

.post-list-item:last-child {
  border-bottom: none;
}

.post-list-item:hover {
  background-color: #fafbfc;
}

.post-main {
  flex: 1;
  min-width: 0;
}

.post-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
}

.post-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: var(--line-height-heading);
}

.post-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
}

.meta-author {
  color: var(--color-text-regular);
}

.meta-time {
  color: var(--color-text-placeholder);
}

.post-preview {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.post-stats {
  display: flex;
  gap: var(--spacing-md);
  flex-shrink: 0;
  margin-left: var(--spacing-md);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
