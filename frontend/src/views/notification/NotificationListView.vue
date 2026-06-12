<template>
  <div class="notifications-page">
    <div class="content-container">
      <PageHeader
        title="通知"
        :breadcrumbs="[{ label: '首页', to: { name: 'Home' } }, { label: '通知' }]"
      >
        <template #actions>
          <el-button
            v-if="store.notifications.length && store.unreadCount > 0"
            text
            type="primary"
            @click="handleMarkAllRead"
          >
            全部标为已读
          </el-button>
        </template>
      </PageHeader>

      <LoadingSkeleton v-if="store.loading" type="list-item" :count="5" />
      <EmptyState
        v-else-if="!store.notifications.length"
        title="暂无通知"
        description="当有人回复或点赞你的内容时，会在这里显示"
      />
      <div v-else class="notification-list">
        <div
          v-for="item in store.notifications"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.is_read }"
          @click="handleClick(item)"
        >
          <div class="notif-left">
            <span v-if="!item.is_read" class="unread-dot" />
            <div class="notif-body">
              <p class="notif-title">
                <span v-if="item.actor" class="actor-name">{{
                  item.actor.nickname || item.actor.username
                }}</span>
                {{ typeLabel(item.type) }}
              </p>
              <p class="notif-content">{{ item.content }}</p>
              <p class="notif-time">{{ formatTimeAgo(item.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>

      <PaginationBar
        v-if="store.pagination.total > store.pagination.pageSize"
        :current-page="store.pagination.page"
        :page-size="store.pagination.pageSize"
        :total="store.pagination.total"
        @page-change="(p: number) => store.fetchNotifications(p)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notifications'
import { NOTIFICATION_TYPE_MAP } from '@/utils/constants'
import { formatTimeAgo } from '@/utils/format'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import type { NotificationRead } from '@/types/notification'

const store = useNotificationStore()
const router = useRouter()

function typeLabel(type: string): string {
  return NOTIFICATION_TYPE_MAP[type] || type
}

function handleClick(item: NotificationRead) {
  if (!item.is_read) store.markRead(item.id)
  if (item.related_type === 'post' && item.related_id) {
    router.push(`/posts/${item.related_id}`)
  }
}

async function handleMarkAllRead() {
  await store.markAllRead()
}

onMounted(() => {
  store.fetchNotifications()
})
</script>

<style scoped>
.notifications-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.notification-list {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
}

.notification-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: var(--color-bg-page);
}

.notification-item.unread {
  background: var(--el-color-primary-light-9, #ecf5ff);
}

.notif-left {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  margin-top: 6px;
  flex-shrink: 0;
}

.notif-body {
  flex: 1;
}

.notif-title {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.actor-name {
  font-weight: 600;
  color: var(--color-primary);
}

.notif-content {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.notif-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
}
</style>
