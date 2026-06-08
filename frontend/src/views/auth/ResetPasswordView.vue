<template>
  <div class="reset-password-page">
    <div class="form-card">
      <h1>修改密码</h1>
      <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="当前密码" :error="errors.old">
          <el-input v-model="form.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" :error="errors.new">
          <el-input
            v-model="form.new_password"
            type="password"
            show-password
            placeholder="至少 8 个字符"
          />
        </el-form-item>
        <el-form-item label="确认新密码" :error="errors.confirm">
          <el-input v-model="form.confirm_password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="submitting" @click="handleSubmit">
          确认修改
        </el-button>
      </el-form>
      <p class="back-link">
        <router-link to="/profile">← 返回个人中心</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { validatePassword } from '@/utils/validation'

const router = useRouter()
const authStore = useAuthStore()
const submitting = ref(false)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const errors = reactive({ old: '', new: '', confirm: '' })

async function handleSubmit() {
  errors.old = ''
  errors.new = ''
  errors.confirm = ''

  if (!form.old_password) {
    errors.old = '请输入当前密码'
    return
  }
  const v = validatePassword(form.new_password)
  if (v !== true) {
    errors.new = v
    return
  }
  if (form.new_password !== form.confirm_password) {
    errors.confirm = '两次输入的密码不一致'
    return
  }

  submitting.value = true
  try {
    await authAPI.resetPassword({
      old_password: form.old_password,
      new_password: form.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    await authStore.logout()
    router.push('/login')
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    const detail: string = e.response?.data?.detail || ''
    if (detail) {
      errors.new = detail
    } else {
      ElMessage.error('密码修改失败')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.reset-password-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
  padding: var(--spacing-xl) var(--spacing-md);
}

.form-card {
  width: 100%;
  max-width: 400px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
}

.form-card h1 {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: var(--spacing-lg);
}

.back-link {
  text-align: center;
  margin-top: var(--spacing-md);
  font-size: var(--font-size-sm);
}
</style>
