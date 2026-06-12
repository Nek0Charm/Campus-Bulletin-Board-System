<template>
  <div class="featured-posts-page">
    <div class="content-container">
      <PageHeader
        title="精选帖子"
        :breadcrumbs="[{ label: '首页', to: { name: 'Home' } }, { label: '精选帖子' }]"
      >
        <p class="page-desc">管理员推荐的高质量内容</p>
      </PageHeader>

      <LoadingSkeleton v-if="loading" type="list-item" :count="5" />
      <ErrorState v-else-if="error" :message="error" @retry="fetchPosts" />
      <EmptyState
        v-else-if="!posts.length"
        title="暂无精选"
        description="管理员还没有精选任何帖子"
      />
      <div v-else class="post-list-wrapper">
        <TransitionGroup name="list-item" tag="div">
          <PostListItem v-for="post in posts" :key="post.id" :post="post" @click="goToPost" />
        </TransitionGroup>
        <PaginationBar
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          @page-change="(p: number) => fetchPosts(p)"
          @size-change="(s: number) => fetchPosts(pagination.page, s)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { postsAPI } from '@/api/posts'
import PostListItem from '@/components/post/PostListItem.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import type { PostRead } from '@/types/post'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'

const router = useRouter()
const posts = ref<PostRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const pagination = reactive({
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,
})

async function fetchPosts(page = 1, pageSize = pagination.pageSize) {
  loading.value = true
  error.value = null
  try {
    const data = await postsAPI.getPosts({
      page,
      page_size: pageSize,
      sort_by: 'created_at',
      is_featured: true,
    })
    posts.value = data.items
    pagination.page = data.pagination.page
    pagination.pageSize = data.pagination.page_size
    pagination.total = data.pagination.total
  } catch {
    error.value = '加载帖子失败'
  } finally {
    loading.value = false
  }
}

function goToPost(postId: string) {
  router.push(`/posts/${postId}`)
}

onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.featured-posts-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.page-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.post-list-wrapper {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}
</style>
