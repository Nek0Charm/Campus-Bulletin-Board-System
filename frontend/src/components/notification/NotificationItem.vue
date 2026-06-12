<template>
  <div class="notification-item" :class="{ unread: !notification.is_read }" @click="handleClick">
    <span class="notif-dot" :class="{ read: notification.is_read }" />
    <div class="notif-content">
      <p class="notif-text">
        <strong v-if="notification.actor">{{
          notification.actor.nickname || notification.actor.username
        }}</strong>
        {{ NOTIFICATION_TYPE_MAP[notification.type] || '操作了' }}
        <span v-if="notification.title">{{ notification.title }}</span>
      </p>
      <span class="notif-time">{{ formatTimeAgo(notification.created_at) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NotificationRead } from '@/types/notification'
import { formatTimeAgo } from '@/utils/format'
import { NOTIFICATION_TYPE_MAP } from '@/utils/constants'

const props = defineProps<{ notification: NotificationRead }>()
const emit = defineEmits<{ click: [notification: NotificationRead] }>()

function handleClick() {
  emit('click', props.notification)
}
</script>

<style scoped>
.notification-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) 0;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border-list);
  transition: background var(--transition-fast);
}

.notification-item:hover {
  background: #fafbfc;
}

.notification-item.unread {
  background: #f0f7ff;
}

.notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
  margin-top: 6px;
}

.notif-dot.read {
  background: var(--color-border);
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-regular);
  line-height: var(--line-height-base);
  margin-bottom: 2px;
}

.notif-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
}
</style>
