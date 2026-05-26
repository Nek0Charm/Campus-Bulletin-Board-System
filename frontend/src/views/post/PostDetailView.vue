<template>
  <div class="post-detail-page">
    <div class="content-container">
      <el-breadcrumb separator=">">
        <el-breadcrumb-item :to="{ name: 'Home' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="backRoute">板块</el-breadcrumb-item>
        <el-breadcrumb-item>{{ post?.title || '帖子详情' }}</el-breadcrumb-item>
      </el-breadcrumb>

      <!-- Loading / Error / Not Found -->
      <LoadingSkeleton v-if="loading" type="detail" />
      <ErrorState v-else-if="error" :message="error" @retry="loadPost" />
      <EmptyState v-else-if="!post" title="帖子不存在" description="该帖子可能已被删除" />

      <!-- Post Detail -->
      <div v-else class="post-detail-card">
        <div class="post-header">
          <div class="post-title-row">
            <PostStatusTag :is-pinned="post.is_pinned" :is-featured="post.is_featured" />
            <h1>{{ post.title }}</h1>
          </div>
          <div class="post-meta">
            <UserAvatar :name="post.author?.nickname || post.author?.username" :size="28" />
            <span class="meta-author">{{ post.author?.nickname || post.author?.username }}</span>
            <span class="meta-time">{{ formatDate(post.created_at) }}</span>
            <span class="meta-views">👁 {{ post.view_count }}</span>
          </div>
        </div>

        <!-- Author/Admin actions -->
        <div class="post-actions" v-if="canEdit">
          <el-button v-if="isAuthor" size="small" @click="$router.push(`/posts/${post.id}/edit`)">
            <el-icon><Edit /></el-icon>编辑
          </el-button>
          <el-button v-if="isAuthor" size="small" type="danger" @click="confirmDelete">
            <el-icon><Delete /></el-icon>删除
          </el-button>
          <el-button v-if="authStore.isAdmin" size="small" @click="togglePin">
            {{ post.is_pinned ? '取消置顶' : '置顶' }}
          </el-button>
          <el-button v-if="authStore.isAdmin" size="small" @click="toggleFeature">
            {{ post.is_featured ? '取消加精' : '加精' }}
          </el-button>
        </div>

        <el-divider />

        <!-- Post Content -->
        <div class="post-content" v-html="sanitizeRichHTML(post.content ?? '')" />

        <el-divider />

        <!-- Interaction bar -->
        <div class="interaction-bar">
          <el-button :type="liked ? 'danger' : 'default'" @click="handleLike">
            <el-icon><StarFilled v-if="liked" /><Star v-else /></el-icon>
            {{ post.like_count }}
          </el-button>
          <span class="interaction-stat">
            <el-icon><ChatDotRound /></el-icon> {{ post.comment_count }}
          </span>
        </div>
      </div>

      <!-- Comments Section -->
      <div v-if="post" class="comments-section">
        <LoadingSkeleton v-if="commentsLoading" type="list-item" :count="3" />
        <div v-else>
          <CommentTree
            :comments="comments"
            :total-count="post.comment_count"
            :liked-set="likedComments"
            @reply="handleReply"
            @toggle-like="handleCommentLike"
            @delete="handleCommentDelete"
          />
        </div>

        <!-- Comment Form -->
        <div class="comment-input-area">
          <template v-if="authStore.isAuthenticated">
            <CommentForm :reply-to="replyTo" @submit="handleCommentSubmit" @cancel="replyTo = ''" />
          </template>
          <div v-else class="login-prompt">
            <el-alert type="info" :closable="false" show-icon>
              请<router-link to="/login">登录</router-link>后参与评论
            </el-alert>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, Star, StarFilled, ChatDotRound } from '@element-plus/icons-vue'
import { sanitizeRichHTML } from '@/utils/sanitize'
import { usePostStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import { postsAPI } from '@/api/posts'
import { likesAPI } from '@/api/likes'
import { commentsAPI } from '@/api/comments'
import PostStatusTag from '@/components/post/PostStatusTag.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import CommentTree from '@/components/comment/CommentTree.vue'
import CommentForm from '@/components/comment/CommentForm.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatDate } from '@/utils/format'
import type { CommentRead } from '@/types/comment'

const route = useRoute()
const router = useRouter()
const postStore = usePostStore()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)
const liked = ref(false)

const post = computed(() => postStore.currentPost)

const isAuthor = computed(() => {
  return authStore.currentUser?.id && post.value?.author?.id === authStore.currentUser.id
})
const canEdit = computed(() => isAuthor.value || authStore.isAdmin)

const backRoute = computed(() => {
  if (post.value?.board_id) return { name: 'Home' }
  return { name: 'Home' }
})

async function loadPost() {
  loading.value = true
  error.value = null
  try {
    await postStore.fetchPostById(route.params.id as string)
  } catch {
    error.value = '加载帖子失败'
  } finally {
    loading.value = false
  }
}

async function handleLike() {
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    if (liked.value) {
      await likesAPI.unlikePost(post.value!.id)
      postStore.updateLikeCount(post.value!.id, -1)
      liked.value = false
    } else {
      await likesAPI.likePost(post.value!.id)
      postStore.updateLikeCount(post.value!.id, 1)
      liked.value = true
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function togglePin() {
  if (!post.value) return
  await postsAPI.pinPost(post.value.id, !post.value.is_pinned)
  post.value.is_pinned = !post.value.is_pinned
  ElMessage.success(post.value.is_pinned ? '已置顶' : '已取消置顶')
}

async function toggleFeature() {
  if (!post.value) return
  await postsAPI.featurePost(post.value.id, !post.value.is_featured)
  post.value.is_featured = !post.value.is_featured
  ElMessage.success(post.value.is_featured ? '已加精' : '已取消加精')
}

async function confirmDelete() {
  try {
    await ElMessageBox.confirm('确定删除这篇帖子？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await postStore.deletePost(post.value!.id)
    ElMessage.success('已删除')
    router.push('/')
  } catch {
    /* canceled */
  }
}

// Comments
const comments = ref<CommentRead[]>([])
const commentsLoading = ref(false)
const likedComments = ref(new Set<string>())
const replyTo = ref('')
const replyToCommentId = ref<string | null>(null)

async function loadComments() {
  commentsLoading.value = true
  try {
    const data = await commentsAPI.getComments(route.params.id as string)
    comments.value = data.items
  } catch {
    /* silent */
  } finally {
    commentsLoading.value = false
  }
}

function handleReply(commentId: string, authorName: string) {
  replyTo.value = authorName
  replyToCommentId.value = commentId
}

async function handleCommentSubmit(content: string) {
  try {
    await commentsAPI.createComment(post.value!.id, {
      content,
      parent_comment_id: replyToCommentId.value,
    })
    ElMessage.success('评论成功')
    replyTo.value = ''
    replyToCommentId.value = null
    await loadComments()
  } catch {
    ElMessage.error('评论失败')
  }
}

async function handleCommentDelete(commentId: string) {
  try {
    await ElMessageBox.confirm('确定删除这条评论？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await commentsAPI.deleteComment(commentId)
    ElMessage.success('已删除')
    await loadComments()
  } catch {
    /* canceled */
  }
}

async function handleCommentLike(commentId: string) {
  try {
    if (likedComments.value.has(commentId)) {
      await likesAPI.unlikeComment(commentId)
      likedComments.value.delete(commentId)
    } else {
      await likesAPI.likeComment(commentId)
      likedComments.value.add(commentId)
    }
  } catch {
    ElMessage.error('操作失败')
  }
}
onMounted(() => {
  loadPost()
  loadComments()
})
</script>

<style scoped>
.post-detail-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.post-detail-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  margin-top: var(--spacing-md);
}

.post-header {
  margin-bottom: var(--spacing-md);
}

.post-title-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.post-title-row h1 {
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.post-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.meta-author {
  color: var(--color-text-regular);
  font-weight: 500;
}

.meta-time {
  color: var(--color-text-placeholder);
}

.meta-views {
  color: var(--color-text-placeholder);
}

.post-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.post-content {
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
  color: var(--color-text-primary);
  min-height: 100px;
}

.interaction-bar {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
}

.interaction-stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.comments-section {
  margin-top: var(--spacing-lg);
}

.comment-input-area {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
}

.login-prompt {
  padding: var(--spacing-sm) 0;
}
</style>
