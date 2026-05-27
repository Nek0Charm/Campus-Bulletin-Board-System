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
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { boardsAPI } from '@/api/boards'

import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { Board } from '@/types/board'

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
</style>
