<template>
  <div class="comment-tree">
    <div class="comment-header-bar">
      <h3>{{ totalCount }} 条评论</h3>
    </div>
    <TransitionGroup name="list-item" tag="div">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :depth="0"
        :liked-set="likedSet"
        @reply="(id, name) => emitReply(id, name)"
        @toggle-like="(id) => emitToggleLike(id)"
        @delete="(id) => emitDelete(id)"
      />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import CommentItem from './CommentItem.vue'
import type { CommentRead } from '@/types/comment'

defineProps<{
  comments: CommentRead[]
  totalCount: number
  likedSet: Set<string>
}>()

const emit = defineEmits<{
  reply: [commentId: string, authorName: string]
  'toggle-like': [commentId: string]
  delete: [commentId: string]
}>()

function emitReply(commentId: string, authorName: string) {
  emit('reply', commentId, authorName)
}

function emitToggleLike(commentId: string) {
  emit('toggle-like', commentId)
}

function emitDelete(commentId: string) {
  emit('delete', commentId)
}
</script>

<style scoped>
.comment-tree {
  margin-top: var(--spacing-lg);
}

.comment-header-bar {
  margin-bottom: var(--spacing-md);
}

.comment-header-bar h3 {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
}
</style>
