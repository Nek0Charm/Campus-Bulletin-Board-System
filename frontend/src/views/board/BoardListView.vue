<template>
  <div class="board-list-page">
    <div class="content-container">
      <PageHeader
        title="版面列表"
        :breadcrumbs="[{ label: '首页', to: { name: 'Home' } }, { label: '版面列表' }]"
      >
        <p class="page-desc">浏览所有板块，找到你感兴趣的讨论</p>
      </PageHeader>

      <LoadingSkeleton v-if="boardStore.loading" type="card" :count="6" />
      <ErrorState
        v-else-if="boardStore.error"
        :message="boardStore.error"
        @retry="boardStore.fetchBoards(true)"
      />
      <EmptyState
        v-else-if="!boardStore.boards.length"
        title="暂无板块"
        description="管理员还没有创建任何板块"
      />

      <div v-else class="board-grid">
        <BoardCard
          v-for="board in boardStore.boards"
          :key="board.id"
          :board="board"
          @click="goToBoard(board.slug)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useBoardStore } from '@/stores/boards'
import BoardCard from '@/components/board/BoardCard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const boardStore = useBoardStore()
const router = useRouter()

onMounted(() => {
  boardStore.fetchBoards()
})

function goToBoard(slug: string) {
  router.push(`/boards/${slug}`)
}
</script>

<style scoped>
.board-list-page {
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
</style>
