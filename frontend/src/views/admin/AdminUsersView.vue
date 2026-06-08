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
        <el-table-column label="操作" width="260">
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
            <template v-if="isUserMuted(row)">
              <el-button size="small" type="info" @click="handleUnmute(row)"> 解除禁言 </el-button>
            </template>
            <template v-else>
              <el-button size="small" type="warning" @click="openMuteDialog(row)"> 禁言 </el-button>
            </template>
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

    <!-- Mute Dialog -->
    <el-dialog v-model="muteDialogVisible" title="禁言用户" width="420px">
      <p style="margin-bottom: 16px">
        将用户 <strong>{{ muteTarget?.nickname || muteTarget?.username }}</strong> 禁言
      </p>
      <div class="mute-presets">
        <el-button
          v-for="preset in MUTE_PRESETS"
          :key="preset.label"
          :type="muteDuration === preset.minutes ? 'primary' : ''"
          @click="muteDuration = preset.minutes"
        >
          {{ preset.label }}
        </el-button>
      </div>
      <el-form-item label="自定义时长（分钟）" style="margin-top: 16px">
        <el-input-number v-model="muteDuration" :min="1" :max="43200" />
      </el-form-item>
      <template #footer>
        <el-button @click="muteDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="muting" @click="handleMute"> 确认禁言 </el-button>
      </template>
    </el-dialog>
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

const MUTE_PRESETS = [
  { label: '10分钟', minutes: 10 },
  { label: '1小时', minutes: 60 },
  { label: '6小时', minutes: 360 },
  { label: '24小时', minutes: 1440 },
  { label: '7天', minutes: 10080 },
]

const users = ref<User[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const pagination = reactive({
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  total: 0,
})
const muteDialogVisible = ref(false)
const muteTarget = ref<User | null>(null)
const muteDuration = ref(60)
const muting = ref(false)

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

function isUserMuted(user: User): boolean {
  if (!user.muted_until) return false
  return new Date(user.muted_until) > new Date()
}

function openMuteDialog(user: User) {
  muteTarget.value = user
  muteDuration.value = 60
  muteDialogVisible.value = true
}

async function handleMute() {
  if (!muteTarget.value) return
  muting.value = true
  try {
    await adminAPI.muteUser(muteTarget.value.id, muteDuration.value)
    ElMessage.success('已禁言')
    muteDialogVisible.value = false
    const u = users.value.find((u) => u.id === muteTarget.value!.id)
    if (u) {
      const until = new Date(Date.now() + muteDuration.value * 60000)
      u.muted_until = until.toISOString()
    }
  } catch {
    ElMessage.error('禁言失败')
  } finally {
    muting.value = false
  }
}

async function handleUnmute(user: User) {
  try {
    await adminAPI.unmuteUser(user.id)
    ElMessage.success('已解除禁言')
    const u = users.value.find((u) => u.id === user.id)
    if (u) u.muted_until = null
  } catch {
    ElMessage.error('操作失败')
  }
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
