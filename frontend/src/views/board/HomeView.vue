<template>
  <div class="home-page">
    <!-- Announcements -->
    <section v-if="announcements.length" class="section section-announcements">
      <div class="announce-list">
        <div v-for="item in announcements" :key="item.id" class="announce-item">
          <div class="announce-item-header">
            <el-icon :size="16" class="announce-icon"><Bell /></el-icon>
            <span class="announce-title">{{ item.title }}</span>
            <span class="announce-time">{{ formatDate(item.created_at) }}</span>
          </div>
          <p class="announce-content">{{ item.content }}</p>
        </div>
      </div>
    </section>

    <!-- Boards -->
    <section class="section section-boards">
      <div class="section-header">
        <h2 class="section-title">热门板块</h2>
        <router-link to="/boards" class="section-more">
          查看全部 <el-icon :size="14"><ArrowRight /></el-icon>
        </router-link>
      </div>

      <LoadingSkeleton v-if="boardLoading" type="card" :count="4" />
      <div v-else-if="boards.length" class="board-grid">
        <BoardCard
          v-for="board in boards.slice(0, 6)"
          :key="board.id"
          :board="board"
          @click="goToBoard(board.slug)"
        />
      </div>
      <EmptyState v-else title="暂无板块" />
    </section>

    <!-- Latest Posts -->
    <section class="section section-posts">
      <div class="section-header">
        <h2 class="section-title">最新帖子</h2>
        <router-link to="/latest" class="section-more">
          查看更多 <el-icon :size="14"><ArrowRight /></el-icon>
        </router-link>
      </div>

      <LoadingSkeleton v-if="postLoading" type="list-item" :count="5" />
      <ErrorState v-else-if="postError" :message="postError" @retry="fetchLatestPosts" />
      <EmptyState v-else-if="!latestPosts.length" title="暂无帖子" description="还没有任何人发帖" />
      <div v-else class="post-list-wrapper">
        <PostListItem
          v-for="post in latestPosts"
          :key="post.id"
          :post="post"
          @click="goToPost(post.id)"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Bell } from '@element-plus/icons-vue'
import { useBoardStore } from '@/stores/boards'
import { postsAPI } from '@/api/posts'
import { announcementsAPI } from '@/api/announcements'
import BoardCard from '@/components/board/BoardCard.vue'
import PostListItem from '@/components/post/PostListItem.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatDate } from '@/utils/format'
import type { PostRead } from '@/types/post'
import type { Board } from '@/types/board'
import type { AnnouncementRead } from '@/types/announcement'

const router = useRouter()
const boardStore = useBoardStore()

const announcements = ref<AnnouncementRead[]>([])
const boardLoading = ref(false)
const boards = ref<Board[]>([])
const latestPosts = ref<PostRead[]>([])
const postLoading = ref(false)
const postError = ref<string | null>(null)

function goToBoard(slug: string) {
  router.push(`/boards/${slug}`)
}

function goToPost(postId: string) {
  router.push(`/posts/${postId}`)
}

async function fetchBoards() {
  boardLoading.value = true
  try {
    await boardStore.fetchBoards()
    boards.value = boardStore.boards
  } finally {
    boardLoading.value = false
  }
}

async function fetchAnnouncements() {
  try {
    announcements.value = await announcementsAPI.getAnnouncements()
  } catch {
    /* silent — announcements are optional */
  }
}

async function fetchLatestPosts() {
  postLoading.value = true
  postError.value = null
  try {
    const data = await postsAPI.getPosts({ page: 1, page_size: 8, sort_by: 'created_at' })
    latestPosts.value = data.items
  } catch {
    postError.value = '加载帖子失败'
  } finally {
    postLoading.value = false
  }
}

onMounted(() => {
  fetchAnnouncements()
  fetchBoards()
  fetchLatestPosts()
})
</script>

<style scoped>
.home-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

/* ── Sections ── */

.section {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: 0 var(--spacing-md) var(--spacing-xl);
}

.section-boards {
  padding-top: var(--spacing-xl);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.section-more {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.section-more:hover {
  color: var(--color-primary);
}

/* ── Announcements ── */

.section-announcements {
  padding-top: var(--spacing-lg);
  padding-bottom: 0;
}

.announce-list {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-left: 3px solid var(--color-warning);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.announce-item {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border-list);
}

.announce-item:last-child {
  border-bottom: none;
}

.announce-item-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.announce-icon {
  color: var(--color-warning);
  flex-shrink: 0;
}

.announce-title {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.announce-time {
  color: var(--color-text-placeholder);
  font-size: var(--font-size-xs);
  flex-shrink: 0;
}

.announce-content {
  margin: var(--spacing-xs) 0 0 24px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Boards ── */

.board-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-md);
}

@media (min-width: 768px) {
  .board-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-lg);
  }
}

@media (min-width: 1024px) {
  .board-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-lg);
  }
}

/* ── Posts ── */

.post-list-wrapper {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

/* ── Responsive ── */

@media (max-width: 767px) {
  .section {
    padding: 0 var(--spacing-sm) var(--spacing-lg);
  }

  .section-announcements {
    padding-top: var(--spacing-md);
    padding-bottom: 0;
  }

  .section-boards {
    padding-top: var(--spacing-lg);
  }

  .announce-time {
    display: none;
  }

  .announce-content {
    -webkit-line-clamp: 2;
  }
}
</style>
