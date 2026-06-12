<template>
  <div class="user-posts-page">
    <div class="content-container">
      <PageHeader
        title="我的帖子"
        :breadcrumbs="[
          { label: '首页', to: { name: 'Home' } },
          { label: '个人中心', to: { name: 'Profile' } },
          { label: '我的帖子' },
        ]"
      />

      <LoadingSkeleton v-if="loading" type="list-item" :count="5" />
      <ErrorState v-else-if="error" :message="error" @retry="fetchMyPosts" />
      <EmptyState
        v-else-if="!posts.length"
        title="暂无帖子"
        description="你还没有发布过帖子"
        action-text="去发帖"
        @action="$router.push('/posts/new')"
      />
      <div v-else class="post-list-wrapper">
        <TransitionGroup name="list-item" tag="div">
          <PostListItem
            v-for="post in posts"
            :key="post.id"
            :post="post"
            @click="$router.push(`/posts/${post.id}`)"
          />
        </TransitionGroup>
        <PaginationBar
          v-if="pagination.total > pagination.pageSize"
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          @page-change="(p: number) => fetchMyPosts(p)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { postsAPI } from '@/api/posts'
import { useAuthStore } from '@/stores/auth'
import PostListItem from '@/components/post/PostListItem.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import type { PostRead } from '@/types/post'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'

const authStore = useAuthStore()

const posts = ref<PostRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const pagination = reactive({
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,
})

async function fetchMyPosts(page = 1) {
  loading.value = true
  error.value = null
  try {
    const data = await postsAPI.getPosts({
      page,
      page_size: pagination.pageSize,
      author_id: authStore.currentUser?.id,
    })
    posts.value = data.items
    Object.assign(pagination, data.pagination)
  } catch {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchMyPosts())
</script>

<style scoped>
.user-posts-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.post-list-wrapper {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}
</style>
