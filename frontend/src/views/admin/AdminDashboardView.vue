<template>
  <div class="admin-dashboard">
    <h1>统计面板</h1>

    <LoadingSkeleton v-if="loading" type="card" :count="4" />
    <ErrorState v-else-if="error" :message="error" @retry="fetchStats" />
    <div v-else class="stats-grid">
      <AdminStatsCard label="用户总数" :value="stats.total_users" icon="user" />
      <AdminStatsCard label="帖子总数" :value="stats.total_posts" icon="post" />
      <AdminStatsCard label="评论总数" :value="stats.total_comments" icon="comment" />
      <AdminStatsCard label="今日新帖" :value="stats.new_posts_today" icon="trend" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { adminAPI } from '@/api/admin'
import type { AdminStats } from '@/api/admin'
import AdminStatsCard from '@/components/admin/AdminStatsCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'

const loading = ref(false)
const error = ref<string | null>(null)
const stats = reactive<AdminStats>({
  total_users: 0,
  total_posts: 0,
  total_comments: 0,
  new_posts_today: 0,
})

async function fetchStats() {
  loading.value = true
  error.value = null
  try {
    const data = await adminAPI.getStats()
    Object.assign(stats, data)
  } catch {
    error.value = '加载统计数据失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchStats())
</script>

<style scoped>
.admin-dashboard h1 {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

@media (min-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
