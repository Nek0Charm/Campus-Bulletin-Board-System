<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo">
        <el-icon :size="24"><ChatDotRound /></el-icon>
        <span class="logo-text">校园论坛</span>
      </router-link>
    </div>
    <div class="header-center">
      <el-input
        v-model="searchKeyword"
        class="header-search"
        size="small"
        clearable
        placeholder="搜索帖子"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    <div class="header-right">
      <template v-if="authStore.isAuthenticated">
        <NotificationBell />
        <el-dropdown trigger="click">
          <span class="user-dropdown">
            <UserAvatar
              :src="authStore.currentUser?.avatar_url"
              :name="authStore.currentUser?.nickname || authStore.currentUser?.username"
              :size="32"
            />
            <span class="username">{{
              authStore.currentUser?.nickname || authStore.currentUser?.username
            }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="$router.push('/profile')">
                <el-icon><User /></el-icon>个人中心
              </el-dropdown-item>
              <el-dropdown-item @click="$router.push('/notifications')">
                <el-icon><Bell /></el-icon>通知
              </el-dropdown-item>
              <el-dropdown-item v-if="authStore.isAdmin" @click="$router.push('/admin')">
                <el-icon><Setting /></el-icon>管理后台
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
      <template v-else>
        <el-button @click="$router.push('/login')">登录</el-button>
      </template>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Bell, ChatDotRound, Search, Setting, SwitchButton, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'
import NotificationBell from '@/components/notification/NotificationBell.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const searchKeyword = ref('')

async function handleLogout() {
  await authStore.logout()
  router.push('/')
}

function routeQueryValue(value: unknown): string {
  if (Array.isArray(value)) return String(value[0] || '')
  return value ? String(value) : ''
}

function handleSearch() {
  const q = searchKeyword.value.trim()
  if (!q) {
    router.push({ name: 'Search' })
    return
  }
  router.push({ name: 'Search', query: { q } })
}

watch(
  () => route.query.q,
  (q) => {
    searchKeyword.value = routeQueryValue(q)
  },
  { immediate: true },
)
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 var(--spacing-lg);
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border-list);
  box-shadow: none;
}

.header-left {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-primary);
  font-size: var(--font-size-lg);
  font-weight: 700;
  text-decoration: none;
}

.logo-text {
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex: 0 0 auto;
}

.header-center {
  flex: 1;
  min-width: 120px;
  display: flex;
  justify-content: center;
  padding: 0 var(--spacing-lg);
}

.header-search {
  width: 100%;
  max-width: 360px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
}

.username {
  font-size: var(--font-size-sm);
  color: var(--color-text-regular);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .app-header {
    padding: 0 var(--spacing-md);
  }
  .header-center {
    padding: 0 var(--spacing-sm);
  }
  .header-search {
    max-width: 220px;
  }
  .logo-text {
    display: none;
  }
  .username {
    display: none;
  }
}
</style>
