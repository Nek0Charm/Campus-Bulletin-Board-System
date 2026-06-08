<template>
  <div class="board-posts-page">
    <div class="content-container">
      <!-- Breadcrumb -->
      <el-breadcrumb separator=">">
        <el-breadcrumb-item :to="{ name: 'Home' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ boardName }}</el-breadcrumb-item>
      </el-breadcrumb>

      <!-- Board Info -->
      <div class="board-info">
        <h1>
          {{ boardName }}
          <el-tag v-if="isBoardMasterHere" type="warning" size="small" class="bm-badge"
            >版主</el-tag
          >
        </h1>
        <p v-if="boardDesc">{{ boardDesc }}</p>
        <!-- Board Masters -->
        <div v-if="boardMasters.length" class="board-masters">
          <span class="masters-label">版主：</span>
          <span v-for="bm in boardMasters" :key="bm.id" class="master-item">
            <UserAvatar
              :src="bm.user.avatar_url"
              :name="bm.user.nickname || bm.user.username"
              :size="18"
            />
            <span class="master-name">{{ bm.user.nickname || bm.user.username }}</span>
          </span>
        </div>
      </div>

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="sort-bar">
          <el-radio-group v-model="sortBy" size="small" @change="fetchPosts">
            <el-radio-button value="created_at">最新发布</el-radio-button>
          </el-radio-group>
        </div>
        <el-button
          v-if="authStore.isAuthenticated"
          type="primary"
          @click="$router.push('/posts/new')"
        >
          + 发帖
        </el-button>
      </div>

      <!-- Post List -->
      <LoadingSkeleton v-if="loading" type="list-item" :count="5" />
      <ErrorState v-else-if="error" :message="error" @retry="fetchPosts" />
      <EmptyState
        v-else-if="!postStore.postList.length"
        title="暂无帖子"
        description="该板块下还没有帖子"
        :action-text="authStore.isAuthenticated ? '去发帖' : undefined"
        @action="$router.push('/posts/new')"
      />
      <div v-else>
        <PostListItem
          v-for="post in postStore.postList"
          :key="post.id"
          :post="post"
          @click="goToPost"
        />
        <PaginationBar
          :current-page="postStore.pagination.page"
          :page-size="postStore.pagination.pageSize"
          :total="postStore.pagination.total"
          @page-change="(p: number) => fetchPosts(p)"
          @size-change="(s: number) => fetchPosts(postStore.pagination.page, s)"
        />
      </div>
    </div>

    <!-- Mobile FAB -->
    <el-button
      v-if="authStore.isAuthenticated"
      class="fab-btn"
      type="primary"
      circle
      size="large"
      @click="$router.push('/posts/new')"
    >
      <el-icon :size="24"><Plus /></el-icon>
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { usePostStore } from '@/stores/posts'
import { useBoardStore } from '@/stores/boards'
import { useAuthStore } from '@/stores/auth'
import { boardsAPI } from '@/api/boards'
import PostListItem from '@/components/post/PostListItem.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import type { BoardMasterInfo } from '@/types/board'

const route = useRoute()
const router = useRouter()
const postStore = usePostStore()
const boardStore = useBoardStore()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)
const sortBy = ref('created_at')
const slug = route.params.slug as string
const boardName = ref(slug || '')
const boardDesc = ref('')
const boardId = ref<string | null>(null)
const boardMasters = ref<BoardMasterInfo[]>([])

const isBoardMasterHere = computed(() => {
  if (!authStore.currentUser?.id) return false
  return boardMasters.value.some((bm) => bm.user_id === authStore.currentUser!.id)
})

async function fetchPosts(page = 1, pageSize = 20) {
  loading.value = true
  error.value = null
  try {
    // resolve slug to board ID first
    if (!boardStore.boards.length) await boardStore.fetchBoards()
    const board = boardStore.boards.find((b) => b.slug === slug)
    if (!board) {
      error.value = '板块不存在'
      loading.value = false
      return
    }
    boardName.value = board.name
    boardDesc.value = board.description || ''
    boardId.value = board.id

    await Promise.all([
      postStore.fetchPosts({ board_id: board.id, page, page_size: pageSize }),
      fetchBoardMasters(board.id),
    ])
  } catch {
    error.value = '加载帖子失败'
  } finally {
    loading.value = false
  }
}

function goToPost(postId: string) {
  router.push(`/posts/${postId}`)
}

async function fetchBoardMasters(id: string) {
  try {
    boardMasters.value = await boardsAPI.getBoardMasters(id)
  } catch {
    boardMasters.value = []
  }
}

onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.board-posts-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.board-info {
  margin-bottom: var(--spacing-lg);
}

.board-info h1 {
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.board-info p {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.bm-badge {
  vertical-align: middle;
}

.board-masters {
  margin-top: var(--spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.masters-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.master-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: var(--font-size-xs);
  color: var(--color-text-regular);
}

.master-name {
  color: var(--color-text-secondary);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.fab-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 50;
  display: none;
}

@media (max-width: 767px) {
  .fab-btn {
    display: flex;
  }
}
</style>
