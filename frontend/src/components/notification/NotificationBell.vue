<template>
  <span class="notification-bell" @click="$router.push('/notifications')">
    <el-badge :value="displayCount" :hidden="!unreadCount" :max="99">
      <el-icon :size="20"><Bell /></el-icon>
    </el-badge>
  </span>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { useNotificationStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/auth'

const notifStore = useNotificationStore()
const authStore = useAuthStore()

const unreadCount = computed(() => notifStore.unreadCount)
const displayCount = computed(() => (unreadCount.value > 99 ? '99+' : unreadCount.value))

onMounted(() => {
  if (authStore.isAuthenticated) {
    notifStore.startPolling()
  }
})

onUnmounted(() => {
  notifStore.stopPolling()
})
</script>

<style scoped>
.notification-bell {
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: var(--spacing-xs);
  color: var(--color-text-regular);
  transition: color var(--transition-fast);
}

.notification-bell:hover {
  color: var(--color-primary);
}
</style>
