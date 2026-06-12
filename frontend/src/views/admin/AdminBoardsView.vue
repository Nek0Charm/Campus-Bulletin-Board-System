<template>
  <div class="admin-boards">
    <div class="page-toolbar">
      <h1>板块管理</h1>
      <el-button type="primary" @click="openCreateDialog">+ 新建板块</el-button>
    </div>

    <LoadingSkeleton v-if="loading" type="table-row" :count="5" />
    <ErrorState v-else-if="error" :message="error" @retry="fetchBoards" />
    <EmptyState v-else-if="!boards.length" title="暂无板块" />
    <div v-else>
      <el-table :data="boards" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="slug" label="标识" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="180">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="70" />
        <el-table-column label="操作" min-width="320">
          <template #default="{ row }">
            <el-button link size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button link size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            <el-button link size="small" type="warning" @click="openMastersDialog(row)"
              >管理版主</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingBoard ? '编辑板块' : '新建板块'"
      width="480px"
    >
      <el-form :model="form" label-position="top">
        <el-form-item label="名称" :error="formErrors.name">
          <el-input v-model="form.name" placeholder="板块名称" />
        </el-form-item>
        <el-form-item label="标识 (slug)" :error="formErrors.slug">
          <el-input v-model="form.slug" placeholder="英文标识，如 tech" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="可选" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ editingBoard ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Board Masters Dialog -->
    <el-dialog
      v-model="mastersDialogVisible"
      :title="`管理版主 — ${mastersTargetBoard?.name || ''}`"
      width="520px"
    >
      <LoadingSkeleton v-if="mastersLoading" type="table-row" :count="3" />
      <div v-else>
        <p v-if="!boardMasters.length" style="color: var(--color-text-secondary)">暂无版主</p>
        <el-table v-else :data="boardMasters" size="small">
          <el-table-column label="用户名" prop="user.username" />
          <el-table-column label="昵称">
            <template #default="{ row }">
              {{ row.user.nickname || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="handleRemoveMaster(row.user_id)">
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-divider />
        <div class="add-master-row">
          <el-select
            v-model="selectedUserId"
            filterable
            remote
            reserve-keyword
            :remote-method="searchUsers"
            :loading="searchingUsers"
            placeholder="搜索用户名或邮箱"
            style="flex: 1"
            clearable
          >
            <el-option
              v-for="u in searchedUsers"
              :key="u.id"
              :label="`${u.username}${u.nickname ? ' (' + u.nickname + ')' : ''} — ${u.email}`"
              :value="u.id"
            >
              <div class="user-option">
                <span class="user-option-name">{{ u.username }}</span>
                <span v-if="u.nickname" class="user-option-nick">({{ u.nickname }})</span>
                <span class="user-option-email">{{ u.email }}</span>
              </div>
            </el-option>
          </el-select>
          <el-button
            type="primary"
            :loading="addingMaster"
            :disabled="!selectedUserId"
            @click="handleAddMaster"
          >
            添加
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { boardsAPI } from '@/api/boards'
import { adminAPI } from '@/api/admin'

import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { Board, BoardMasterInfo } from '@/types/board'
import type { User } from '@/types/user'

const boards = ref<Board[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const saving = ref(false)
const dialogVisible = ref(false)
const editingBoard = ref<Board | null>(null)

const form = reactive({
  name: '',
  slug: '',
  description: '',
  sort_order: 0,
})
const formErrors = reactive({ name: '', slug: '' })

async function fetchBoards() {
  loading.value = true
  error.value = null
  try {
    boards.value = await boardsAPI.getBoards()
  } catch {
    error.value = '加载板块列表失败'
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingBoard.value = null
  form.name = ''
  form.slug = ''
  form.description = ''
  form.sort_order = 0
  formErrors.name = ''
  formErrors.slug = ''
  dialogVisible.value = true
}

function openEditDialog(board: Board) {
  editingBoard.value = board
  form.name = board.name
  form.slug = board.slug
  form.description = board.description || ''
  form.sort_order = board.sort_order
  formErrors.name = ''
  formErrors.slug = ''
  dialogVisible.value = true
}

async function handleSave() {
  formErrors.name = ''
  formErrors.slug = ''
  if (!form.name.trim()) {
    formErrors.name = '请输入名称'
    return
  }
  if (!form.slug.trim()) {
    formErrors.slug = '请输入标识'
    return
  }

  saving.value = true
  try {
    if (editingBoard.value) {
      await boardsAPI.updateBoard(editingBoard.value.id, { ...form })
      ElMessage.success('已更新')
    } else {
      await boardsAPI.createBoard({ ...form })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await fetchBoards()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(board: Board) {
  try {
    await ElMessageBox.confirm(`确定删除板块「${board.name}」？`, '确认删除', { type: 'warning' })
    await boardsAPI.deleteBoard(board.id)
    ElMessage.success('已删除')
    await fetchBoards()
  } catch {
    /* canceled */
  }
}

// Board Master Management
const mastersDialogVisible = ref(false)
const mastersTargetBoard = ref<Board | null>(null)
const boardMasters = ref<BoardMasterInfo[]>([])
const mastersLoading = ref(false)
const selectedUserId = ref<string | null>(null)
const searchedUsers = ref<User[]>([])
const searchingUsers = ref(false)
const addingMaster = ref(false)

async function openMastersDialog(board: Board) {
  mastersTargetBoard.value = board
  selectedUserId.value = null
  searchedUsers.value = []
  mastersDialogVisible.value = true
  await fetchBoardMasters()
}

async function fetchBoardMasters() {
  if (!mastersTargetBoard.value) return
  mastersLoading.value = true
  try {
    boardMasters.value = await adminAPI.listBoardMasters(mastersTargetBoard.value.id)
  } catch {
    ElMessage.error('加载版主列表失败')
  } finally {
    mastersLoading.value = false
  }
}

async function searchUsers(query: string) {
  if (!query || query.length < 1) {
    searchedUsers.value = []
    return
  }
  searchingUsers.value = true
  try {
    const result = await adminAPI.listUsers({ search: query, page_size: 20 })
    // Exclude users who are already board masters
    const existingIds = new Set(boardMasters.value.map((bm) => bm.user_id))
    searchedUsers.value = result.items.filter((u) => !existingIds.has(u.id))
  } catch {
    searchedUsers.value = []
  } finally {
    searchingUsers.value = false
  }
}

async function handleAddMaster() {
  if (!mastersTargetBoard.value || !selectedUserId.value) {
    ElMessage.warning('请选择用户')
    return
  }
  addingMaster.value = true
  try {
    await adminAPI.addBoardMaster(mastersTargetBoard.value.id, selectedUserId.value)
    ElMessage.success('已添加版主')
    selectedUserId.value = null
    searchedUsers.value = []
    await fetchBoardMasters()
  } catch {
    ElMessage.error('添加失败')
  } finally {
    addingMaster.value = false
  }
}

async function handleRemoveMaster(userId: string) {
  if (!mastersTargetBoard.value) return
  try {
    await adminAPI.removeBoardMaster(mastersTargetBoard.value.id, userId)
    ElMessage.success('已移除版主')
    boardMasters.value = boardMasters.value.filter((bm) => bm.user_id !== userId)
  } catch {
    ElMessage.error('移除失败')
  }
}

onMounted(() => fetchBoards())
</script>

<style scoped>
.admin-boards h1 {
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

.add-master-row {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-option-name {
  font-weight: 500;
}

.user-option-nick {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.user-option-email {
  color: var(--color-text-placeholder);
  font-size: var(--font-size-xs);
  margin-left: auto;
}
</style>
