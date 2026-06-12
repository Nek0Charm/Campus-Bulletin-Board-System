<template>
  <div class="verify-page">
    <div class="verify-card">
      <!-- Loading -->
      <div v-if="loading" class="verify-status">
        <el-icon :size="48" class="spin"><Loading /></el-icon>
        <h2>正在验证邮箱...</h2>
      </div>

      <!-- Success -->
      <div v-else-if="success" class="verify-status">
        <div class="verify-icon success">
          <el-icon :size="48"><CircleCheckFilled /></el-icon>
        </div>
        <h2>邮箱验证成功</h2>
        <p class="verify-desc">您现在可以登录校园论坛了</p>
        <el-button type="primary" @click="$router.push('/login')">去登录</el-button>
      </div>

      <!-- Sent / Check Email -->
      <div v-else-if="showCheckEmail" class="verify-status">
        <div class="verify-icon">
          <el-icon :size="48"><Message /></el-icon>
        </div>
        <h2>验证邮件已发送</h2>
        <p class="verify-desc">
          验证邮件已发送至 <strong>{{ resendForm.email }}</strong
          >，请点击邮件中的链接完成验证。
        </p>
        <p class="verify-desc">如果没有收到邮件，请检查垃圾箱，或点击下方按钮重新发送。</p>
        <div class="resend-section">
          <el-button
            type="primary"
            :loading="resending"
            :disabled="cooldown > 0"
            @click="handleResend"
          >
            <template v-if="cooldown > 0">{{ cooldown }}s 后可重发</template>
            <template v-else>重新发送验证邮件</template>
          </el-button>
        </div>
      </div>

      <!-- Error / Resend -->
      <div v-else class="verify-status">
        <div class="verify-icon error">
          <el-icon :size="48"><WarningFilled /></el-icon>
        </div>
        <h2>{{ errorTitle }}</h2>
        <p class="verify-desc">{{ errorMsg }}</p>

        <div v-if="showResend" class="resend-section">
          <el-form :model="resendForm" label-position="top" style="margin-top: 16px">
            <el-form-item label="邮箱地址">
              <el-input v-model="resendForm.email" placeholder="请输入注册时使用的邮箱" />
            </el-form-item>
            <el-button
              type="primary"
              :loading="resending"
              :disabled="cooldown > 0"
              @click="handleResend"
            >
              <template v-if="cooldown > 0">{{ cooldown }}s 后可重发</template>
              <template v-else>重新发送验证邮件</template>
            </el-button>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheckFilled, WarningFilled, Message } from '@element-plus/icons-vue'
import { authAPI } from '@/api/auth'

const route = useRoute()
const loading = ref(true)
const success = ref(false)
const showCheckEmail = ref(false)
const errorTitle = ref('')
const errorMsg = ref('')
const showResend = ref(false)

const resendForm = reactive({ email: '' })
const resending = ref(false)
const cooldown = ref(0)

onMounted(async () => {
  const token = route.query.token as string | undefined
  const email = route.query.email as string | undefined

  if (!token && email) {
    loading.value = false
    showCheckEmail.value = true
    resendForm.email = email
    return
  }

  if (!token) {
    loading.value = false
    errorTitle.value = '无效的验证链接'
    errorMsg.value = '请检查邮件中的链接是否完整，或重新发送验证邮件。'
    showResend.value = true
    return
  }

  try {
    await authAPI.verifyEmail(token)
    loading.value = false
    success.value = true
  } catch (err: unknown) {
    loading.value = false
    const e = err as { response?: { data?: { detail?: string } }; detail?: string }
    const detail = e.response?.data?.detail || e.detail || ''
    if (detail.includes('expired') || detail.includes('Expired')) {
      errorTitle.value = '验证链接已过期'
      errorMsg.value = '请点击下方按钮重新发送验证邮件。'
    } else if (detail.includes('already verified') || detail.includes('Already')) {
      errorTitle.value = '邮箱已验证'
      errorMsg.value = '您的邮箱已经验证过了，可以直接登录。'
    } else {
      errorTitle.value = '验证失败'
      errorMsg.value = detail || '邮箱验证失败，请稍后重试。'
    }
    showResend.value = true
  }
})

const RESEND_COOLDOWN = 60

async function handleResend() {
  const email = resendForm.email.trim()
  if (!email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  resending.value = true
  try {
    await authAPI.resendVerification({ email })
    ElMessage.success('验证邮件已重新发送，请查收')
    cooldown.value = RESEND_COOLDOWN
    const timer = setInterval(() => {
      cooldown.value--
      if (cooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch {
    ElMessage.error('发送失败，请稍后重试')
  } finally {
    resending.value = false
  }
}
</script>

<style scoped>
.verify-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
  padding: var(--spacing-xl) var(--spacing-md);
}

.verify-card {
  width: 100%;
  max-width: 420px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  border: 1px solid var(--color-border-light);
  text-align: center;
}

.verify-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.verify-icon.success {
  color: var(--color-success);
}
.verify-icon.error {
  color: var(--color-warning);
}

.verify-desc {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin-top: 4px;
}

.resend-section {
  width: 100%;
}

.spin {
  animation: spin 1s linear infinite;
  color: var(--color-primary);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
