<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <el-icon :size="36"><ChatDotRound /></el-icon>
        </div>
        <h1>校园论坛</h1>
      </div>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Login Tab -->
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-position="top">
            <el-form-item label="账号">
              <el-input v-model="loginForm.account" placeholder="用户名或邮箱" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="loginForm.password"
                type="password"
                show-password
                placeholder="请输入密码"
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-button type="primary" style="width: 100%" :loading="loggingIn" @click="handleLogin">
              登 录
            </el-button>
          </el-form>
          <p class="switch-text">
            还没有账号？<el-button type="primary" link @click="activeTab = 'register'"
              >立即注册</el-button
            >
          </p>
        </el-tab-pane>

        <!-- Register Tab -->
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" label-position="top">
            <el-form-item label="用户名" :error="regErrors.username">
              <el-input v-model="registerForm.username" placeholder="3-32 个字符" />
            </el-form-item>
            <el-form-item label="邮箱" :error="regErrors.email">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="registerForm.nickname" placeholder="可选" />
            </el-form-item>
            <el-form-item label="密码" :error="regErrors.password">
              <el-input
                v-model="registerForm.password"
                type="password"
                show-password
                placeholder="至少 8 个字符"
              />
            </el-form-item>
            <el-form-item label="确认密码" :error="regErrors.confirmPassword">
              <el-input
                v-model="confirmPassword"
                type="password"
                show-password
                placeholder="再次输入密码"
              />
            </el-form-item>
            <el-button
              type="primary"
              style="width: 100%"
              :loading="registering"
              @click="handleRegister"
            >
              注 册
            </el-button>
          </el-form>
          <p class="switch-text">
            已有账号？<el-button type="primary" link @click="activeTab = 'login'">去登录</el-button>
          </p>
        </el-tab-pane>
      </el-tabs>

      <!-- Resend verification dialog -->
      <el-dialog v-model="resendDialogVisible" title="邮箱未验证" width="360px" center>
        <p
          style="
            margin-bottom: 12px;
            color: var(--color-text-secondary);
            font-size: var(--font-size-sm);
          "
        >
          您的邮箱尚未验证，请检查邮箱中的验证链接，或重新发送验证邮件。
        </p>
        <el-input v-model="resendEmail" placeholder="请输入注册邮箱" />
        <template #footer>
          <el-button @click="resendDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="resending"
            :disabled="resendCooldown > 0"
            @click="handleResend"
          >
            <template v-if="resendCooldown > 0">{{ resendCooldown }}s 后可重发</template>
            <template v-else>重新发送</template>
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/api/auth'
import type { RegisterRequest } from '@/types/user'
import { validateUsername, validateEmail, validatePassword } from '@/utils/validation'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeTab = ref('login')
const resendDialogVisible = ref(false)
const resendEmail = ref('')
const resending = ref(false)
const resendCooldown = ref(0)
const lastLoginAccount = ref('')

// Login
const loginForm = reactive({ account: '', password: '' })
const loggingIn = ref(false)

function handleTabChange(tab: string) {
  if (typeof tab !== 'string') return
  activeTab.value = tab
}

async function handleLogin() {
  if (!loginForm.account.trim() || !loginForm.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loggingIn.value = true
  try {
    await authStore.login({ account: loginForm.account, password: loginForm.password })
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; detail?: string }
    const detail = e.response?.data?.detail || e.detail || ''
    if (detail.includes('not verified') || detail.includes('Email not verified')) {
      lastLoginAccount.value = loginForm.account
      resendEmail.value = loginForm.account.includes('@') ? loginForm.account : ''
      resendDialogVisible.value = true
    } else if (detail.includes('banned') || detail.includes('inactive')) {
      ElMessage.error('账号已被封禁，无法登录')
    } else {
      ElMessage.error('账号或密码错误')
    }
  } finally {
    loggingIn.value = false
  }
}

// Register
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  nickname: '',
})
const confirmPassword = ref('')
const registering = ref(false)
const regErrors = reactive<Record<string, string>>({})

async function handleRegister() {
  regErrors.username = ''
  regErrors.email = ''
  regErrors.password = ''
  regErrors.confirmPassword = ''

  const u = validateUsername(registerForm.username)
  if (u !== true) {
    regErrors.username = u
    return
  }
  const e = validateEmail(registerForm.email)
  if (e !== true) {
    regErrors.email = e
    return
  }
  const p = validatePassword(registerForm.password)
  if (p !== true) {
    regErrors.password = p
    return
  }
  if (registerForm.password !== confirmPassword.value) {
    regErrors.confirmPassword = '两次输入的密码不一致'
    return
  }

  const payload: RegisterRequest = {
    username: registerForm.username,
    email: registerForm.email,
    password: registerForm.password,
  }
  if (registerForm.nickname.trim()) {
    payload.nickname = registerForm.nickname.trim()
  }

  registering.value = true
  try {
    await authStore.register(payload)
    ElMessage.success('注册成功！请查收验证邮件。')
    router.push({ name: 'VerifyEmail', query: { email: registerForm.email } })
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; detail?: string }
    const detail = e.response?.data?.detail
    ElMessage.error(detail || '注册失败，请稍后重试')
  } finally {
    registering.value = false
  }
}

async function handleResend() {
  const email = resendEmail.value.trim()
  if (!email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  resending.value = true
  try {
    await authAPI.resendVerification({ email })
    ElMessage.success('验证邮件已重新发送，请查收')
    resendDialogVisible.value = false
    resendCooldown.value = 60
    const timer = setInterval(() => {
      resendCooldown.value--
      if (resendCooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    const detail = e.response?.data?.detail
    ElMessage.error(detail || '发送失败，请稍后重试')
  } finally {
    resending.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
  padding: var(--spacing-xl) var(--spacing-md);
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  border: 1px solid var(--color-border-light);
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-lg);
}

.login-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  margin: 0 auto var(--spacing-sm);
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
}

.login-header h1 {
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.switch-text {
  text-align: center;
  margin-top: var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
