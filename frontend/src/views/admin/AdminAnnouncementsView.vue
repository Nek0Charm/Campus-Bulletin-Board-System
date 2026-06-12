<template>
  <div class="admin-announcements">
    <div class="page-header">
      <h1>公告管理</h1>
      <el-button type="primary" @click="openCreate">
        <el-icon :size="16"><Plus /></el-icon>
        发布公告
      </el-button>
    </div>

    <LoadingSkeleton v-if="loading" type="list-item" :count="3" />
    <ErrorState v-else-if="error" :message="error" @retry="fetchAnnouncements" />
    <EmptyState
      v-else-if="!announcements.length"
      title="暂无公告"
      description="还没有创建任何公告"
    />

    <div v-else class="announce-table-wrapper">
      <el-table :data="announcements" stripe>
        <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
              {{ row.is_published ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="有效期" min-width="180">
          <template #default="{ row }">
            <span v-if="row.starts_at || row.ends_at" class="date-range">
              {{ row.starts_at ? formatDate(row.starts_at) : '不限' }}
              —
              {{ row.ends_at ? formatDate(row.ends_at) : '不限' }}
            </span>
            <span v-else class="text-muted">永久有效</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" type="primary" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除这条公告？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button text size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Create / Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑公告' : '发布公告'"
      width="560px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_published" active-text="发布" inactive-text="草稿" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="form.starts_at" type="datetime" placeholder="留空则不限制" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="form.ends_at" type="datetime" placeholder="留空则不限制" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ editingId ? '保存' : '发布' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { adminAPI } from '@/api/admin'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatDate } from '@/utils/format'
import type { AnnouncementRead } from '@/types/announcement'

const announcements = ref<AnnouncementRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const submitting = ref(false)
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const formRef = ref<FormInstance>()

const emptyForm = () => ({
  title: '',
  content: '',
  is_published: true,
  starts_at: null as Date | null,
  ends_at: null as Date | null,
})

const form = reactive(emptyForm())

const rules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}

async function fetchAnnouncements() {
  loading.value = true
  error.value = null
  try {
    announcements.value = await adminAPI.listAnnouncements()
  } catch {
    error.value = '加载公告失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(row: AnnouncementRead) {
  editingId.value = row.id
  form.title = row.title
  form.content = row.content
  form.is_published = row.is_published
  form.starts_at = row.starts_at ? new Date(row.starts_at) : null
  form.ends_at = row.ends_at ? new Date(row.ends_at) : null
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const payload = {
      title: form.title,
      content: form.content,
      is_published: form.is_published,
      starts_at: form.starts_at ? form.starts_at.toISOString() : undefined,
      ends_at: form.ends_at ? form.ends_at.toISOString() : undefined,
    }
    if (editingId.value) {
      await adminAPI.updateAnnouncement(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await adminAPI.createAnnouncement(payload)
      ElMessage.success('已发布')
    }
    dialogVisible.value = false
    await fetchAnnouncements()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await adminAPI.deleteAnnouncement(id)
    ElMessage.success('已删除')
    await fetchAnnouncements()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchAnnouncements()
})
</script>

<style scoped>
.admin-announcements {
  max-width: 960px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.announce-table-wrapper {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.date-range {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.text-muted {
  color: var(--color-text-placeholder);
  font-size: var(--font-size-xs);
}
</style>
