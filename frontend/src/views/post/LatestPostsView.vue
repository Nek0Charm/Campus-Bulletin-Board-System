<template>
  <div class="latest-posts-page">
    <div class="content-container">
      <PageHeader
        title="最新帖子"
        :breadcrumbs="[{ label: '首页', to: { name: 'Home' } }, { label: '最新帖子' }]"
      >
        <div class="toolbar">
          <div class="sort-bar">
            <el-radio-group v-model="sortBy" size="small" @change="fetchPosts">
              <el-radio-button value="created_at">最新发布</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </PageHeader>

      <LoadingSkeleton v-if="loading" type="list-item" :count="5" />
      <ErrorState v-else-if="error" :message="error" @retry="fetchPosts" />
      <EmptyState v-else-if="!posts.length" title="暂无帖子" description="还没有任何帖子发布" />
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
const sortBy = ref('created_at')
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
      sort_by: sortBy.value,
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
.latest-posts-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.post-list-wrapper {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}
</style>
