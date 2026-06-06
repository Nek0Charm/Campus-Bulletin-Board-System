<template>
  <div class="search-page">
    <div class="content-container">
      <el-breadcrumb separator=">">
        <el-breadcrumb-item :to="{ name: 'Home' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>搜索</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="search-header">
        <h1>搜索帖子</h1>
        <div class="keyword-row">
          <el-input
            v-model="keyword"
            clearable
            placeholder="搜索标题或正文"
            @keyup.enter="submitSearch()"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="submitSearch()">搜索</el-button>
        </div>
      </div>

      <div class="filters">
        <el-select
          v-model="selectedBoardId"
          clearable
          placeholder="全部板块"
          @change="handleFilterChange"
        >
          <el-option
            v-for="board in boardStore.boards"
            :key="board.id"
            :label="board.name"
            :value="board.id"
          />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleFilterChange"
        />

        <el-radio-group v-model="sortBy" size="small" @change="handleFilterChange">
          <el-radio-button value="relevance">相关度</el-radio-button>
          <el-radio-button value="hot">热度</el-radio-button>
          <el-radio-button value="time">时间</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="searched && !loading" class="result-summary">
        找到 {{ pagination.total }} 条与“{{ routeKeyword }}”相关的帖子
      </div>

      <LoadingSkeleton v-if="loading" type="list-item" :count="5" />
      <ErrorState v-else-if="error" :message="error" @retry="fetchSearch" />
      <EmptyState
        v-else-if="!searched"
        title="输入关键词开始搜索"
        description="可以按板块、日期范围和排序方式缩小结果"
      />
      <EmptyState
        v-else-if="!results.length"
        title="没有找到相关帖子"
        description="换一个关键词或放宽筛选条件试试"
      />

      <div v-else>
        <PostListItem v-for="post in results" :key="post.id" :post="post" @click="goToPost" />
        <PaginationBar
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          @page-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { searchAPI, type SearchSort } from '@/api/search'
import { useBoardStore } from '@/stores/boards'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'
import type { PostRead } from '@/types/post'
import PostListItem from '@/components/post/PostListItem.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const boardStore = useBoardStore()

const keyword = ref('')
const selectedBoardId = ref<string | undefined>()
const dateRange = ref<string[] | null>(null)
const sortBy = ref<SearchSort>('relevance')
const results = ref<PostRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searched = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,
  totalPages: 0,
})

const routeKeyword = computed(() => queryValue(route.query.q))

function queryValue(value: unknown): string {
  if (Array.isArray(value)) return String(value[0] || '')
  return value ? String(value) : ''
}

function syncFromRoute() {
  keyword.value = queryValue(route.query.q)
  selectedBoardId.value = queryValue(route.query.board_id) || undefined

  const startDate = queryValue(route.query.start_date)
  const endDate = queryValue(route.query.end_date)
  dateRange.value = startDate || endDate ? [startDate, endDate] : null

  const nextSort = queryValue(route.query.sort_by)
  sortBy.value = ['relevance', 'hot', 'time'].includes(nextSort)
    ? (nextSort as SearchSort)
    : 'relevance'

  pagination.page = Number(queryValue(route.query.page)) || 1
  pagination.pageSize = Number(queryValue(route.query.page_size)) || DEFAULT_PAGE_SIZE
}

function buildQuery(page = 1, pageSize = pagination.pageSize) {
  const q = keyword.value.trim()
  const [startDate, endDate] = dateRange.value || []
  return {
    q,
    ...(selectedBoardId.value ? { board_id: selectedBoardId.value } : {}),
    ...(startDate ? { start_date: startDate } : {}),
    ...(endDate ? { end_date: endDate } : {}),
    ...(sortBy.value !== 'relevance' ? { sort_by: sortBy.value } : {}),
    ...(page > 1 ? { page: String(page) } : {}),
    ...(pageSize !== DEFAULT_PAGE_SIZE ? { page_size: String(pageSize) } : {}),
  }
}

function submitSearch(page = 1, pageSize = pagination.pageSize) {
  if (!keyword.value.trim()) {
    router.push({ name: 'Search' })
    return
  }
  router.push({ name: 'Search', query: buildQuery(page, pageSize) })
}

function handleFilterChange() {
  submitSearch(1, pagination.pageSize)
}

function handlePageChange(page: number) {
  submitSearch(page, pagination.pageSize)
}

function handleSizeChange(size: number) {
  submitSearch(1, size)
}

async function fetchSearch() {
  error.value = null
  if (!keyword.value.trim()) {
    searched.value = false
    results.value = []
    Object.assign(pagination, { page: 1, total: 0, totalPages: 0 })
    return
  }

  searched.value = true
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value || []
    const data = await searchAPI.searchPosts({
      q: keyword.value.trim(),
      board_id: selectedBoardId.value,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      sort_by: sortBy.value,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    results.value = data.items
    Object.assign(pagination, {
      page: data.pagination.page,
      pageSize: data.pagination.page_size,
      total: data.pagination.total,
      totalPages: data.pagination.total_pages,
    })
  } catch {
    error.value = '搜索失败'
  } finally {
    loading.value = false
  }
}

function goToPost(postId: string) {
  router.push(`/posts/${postId}`)
}

onMounted(async () => {
  await boardStore.fetchBoards()
  syncFromRoute()
  await fetchSearch()
})

watch(
  () => route.fullPath,
  async () => {
    syncFromRoute()
    await fetchSearch()
  },
)
</script>

<style scoped>
.search-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.search-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--spacing-lg);
  margin: var(--spacing-lg) 0;
}

.search-header h1 {
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.keyword-row {
  display: flex;
  width: min(560px, 100%);
  gap: var(--spacing-sm);
}

.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.filters :deep(.el-select) {
  width: 180px;
}

.filters :deep(.el-date-editor) {
  width: 280px;
}

.result-summary {
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

@media (max-width: 767px) {
  .search-header {
    display: block;
  }

  .search-header h1 {
    margin-bottom: var(--spacing-md);
  }

  .keyword-row,
  .filters :deep(.el-select),
  .filters :deep(.el-date-editor) {
    width: 100%;
  }
}
</style>

