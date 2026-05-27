<template>
  <div class="admin-users">
    <div class="page-toolbar">
      <h1>用户管理</h1>
      <el-input
        v-model="search"
        placeholder="搜索用户名或邮箱"
        clearable
        style="width: 240px"
        @change="fetchUsers"
      />
    </div>

    <LoadingSkeleton v-if="loading" type="table-row" :count="5" />
    <ErrorState v-else-if="error" :message="error" @retry="fetchUsers" />
    <EmptyState v-else-if="!users.length" title="暂无用户" />
    <div v-else>
      <el-table :data="users" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="nickname" label="昵称" min-width="120">
          <template #default="{ row }">
            {{ row.nickname || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="80">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="USER_STATUS_MAP[row.status]?.type || 'info'" size="small">
              {{ USER_STATUS_MAP[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'active'"
              size="small"
              type="warning"
              @click="handleBan(row.id)"
            >
              封禁
            </el-button>
            <el-button
              v-if="row.status === 'banned'"
              size="small"
              type="success"
              @click="handleActivate(row.id)"
            >
              解封
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <PaginationBar
        v-if="pagination.total > pagination.pageSize"
        :current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        @page-change="(p: number) => fetchUsers(p)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '@/api/admin'
import { USER_STATUS_MAP } from '@/utils/constants'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'
import PaginationBar from '@/components/common/PaginationBar.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { User } from '@/types/user'

const users = ref<User[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const pagination = reactive({
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,
})

async function fetchUsers(page = 1) {
  loading.value = true
  error.value = null
  try {
    const data = await adminAPI.listUsers({
      page,
      page_size: pagination.pageSize,
      search: search.value || undefined,
    })
    users.value = data.items
    Object.assign(pagination, data.pagination)
  } catch {
    error.value = '加载用户列表失败'
  } finally {
    loading.value = false
  }
}

async function handleBan(userId: string) {
  try {
    await ElMessageBox.confirm('确定封禁该用户？', '确认', { type: 'warning' })
    await adminAPI.updateUserStatus(userId, 'banned')
    ElMessage.success('已封禁')
    const u = users.value.find((u) => u.id === userId)
    if (u) u.status = 'banned'
  } catch {
    /* canceled */
  }
}

async function handleActivate(userId: string) {
  await adminAPI.updateUserStatus(userId, 'active')
  ElMessage.success('已解封')
  const u = users.value.find((u) => u.id === userId)
  if (u) u.status = 'active'
}

onMounted(() => fetchUsers())
</script>

<style scoped>
.admin-users h1 {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.page-toolbar h1 {
  margin-bottom: 0;
}
</style>
