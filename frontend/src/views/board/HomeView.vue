<template>
  <div class="home-page">
    <div class="content-container">
      <div class="page-hero">
        <h1>校园论坛</h1>
        <p>加入讨论，分享你的校园生活</p>
      </div>

      <h2 class="section-title">板块列表</h2>

      <LoadingSkeleton v-if="boardStore.loading" type="card" :count="6" />
      <ErrorState
        v-else-if="boardStore.error"
        :message="boardStore.error"
        @retry="boardStore.fetchBoards()"
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
.home-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.page-hero {
  text-align: center;
  padding: var(--spacing-xl) 0 var(--spacing-lg);
}

.page-hero h1 {
  font-size: var(--font-size-title);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.page-hero p {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
  color: var(--color-text-primary);
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
