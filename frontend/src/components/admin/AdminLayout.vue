<template>
  <div class="admin-layout">
    <aside class="admin-sidebar" :class="{ collapsed: uiStore.sidebarCollapsed }">
      <div class="sidebar-title">管理后台</div>
      <el-menu :default-active="route.path" router :collapse="uiStore.sidebarCollapsed">
        <el-menu-item index="/admin">
          <el-icon><DataAnalysis /></el-icon>
          <span>统计面板</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/boards">
          <el-icon><Grid /></el-icon>
          <span>板块管理</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <el-button text @click="toggleCollapse">
          <el-icon><Fold v-if="!uiStore.sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
        <el-button text @click="$router.push('/')">
          <el-icon><HomeFilled /></el-icon>
          <span v-if="!uiStore.sidebarCollapsed">返回首页</span>
        </el-button>
      </div>
    </aside>
    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { DataAnalysis, User, Grid, Fold, Expand, HomeFilled } from '@element-plus/icons-vue'
import { useUIStore } from '@/stores/ui'

const route = useRoute()
const uiStore = useUIStore()

function toggleCollapse() {
  uiStore.toggleSidebar()
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.admin-sidebar {
  width: var(--sidebar-width);
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
}

.admin-sidebar.collapsed {
  width: 64px;
}

.sidebar-title {
  padding: var(--spacing-md);
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
  border-bottom: 1px solid var(--color-border-list);
}

.admin-main {
  flex: 1;
  padding: var(--spacing-lg);
  background: #f2f3f5;
  overflow-y: auto;
}

.sidebar-footer {
  margin-top: auto;
  padding: var(--spacing-sm);
  border-top: 1px solid var(--color-border-list);
  display: flex;
  justify-content: center;
  gap: var(--spacing-xs);
}

@media (max-width: 767px) {
  .admin-sidebar {
    width: 64px;
  }
  .sidebar-title {
    display: none;
  }
  .admin-main {
    padding: var(--spacing-md);
  }
}
</style>
