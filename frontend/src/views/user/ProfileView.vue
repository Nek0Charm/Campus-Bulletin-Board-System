<template>
  <div class="profile-page">
    <div class="content-container">
      <el-breadcrumb separator=">">
        <el-breadcrumb-item :to="{ name: 'Home' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>个人中心</el-breadcrumb-item>
      </el-breadcrumb>

      <LoadingSkeleton v-if="loading" type="detail" />
      <ErrorState v-else-if="error" :message="error" @retry="loadProfile" />
      <div v-else-if="user" class="profile-content">
        <!-- Profile card -->
        <div class="profile-card">
          <div class="profile-avatar-section">
            <div class="avatar-upload-wrapper" @click="triggerAvatarUpload">
              <img v-if="user.avatar_url" :src="user.avatar_url" alt="头像" class="avatar-img" />
              <UserAvatar v-else :name="user.nickname || user.username" :size="80" />
              <div class="avatar-overlay">更换头像</div>
            </div>
            <input
              ref="avatarInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              style="display: none"
              @change="handleAvatarChange"
            />
            <AvatarCropDialog
              v-model="showCropDialog"
              :image-src="cropImageSrc"
              @confirm="handleCropConfirm"
            />
            <h2>{{ user.nickname || user.username }}</h2>
            <p class="profile-username">@{{ user.username }}</p>
            <el-tag :type="user.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ user.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </div>
          <div class="profile-stats">
            <div class="stat-item">
              <span class="stat-value">{{ userStats.post_count ?? '-' }}</span>
              <span class="stat-label">帖子</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ userStats.comment_count ?? '-' }}</span>
              <span class="stat-label">评论</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ userStats.like_count ?? '-' }}</span>
              <span class="stat-label">获赞</span>
            </div>
          </div>
        </div>

        <!-- Edit profile -->
        <div class="profile-card">
          <h3>编辑资料</h3>
          <el-form :model="profileForm" label-position="top" @submit.prevent="handleUpdateProfile">
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" placeholder="输入昵称" maxlength="32" />
            </el-form-item>
            <el-button type="primary" :loading="updating" @click="handleUpdateProfile">
              保存
            </el-button>
          </el-form>
        </div>

        <!-- Security -->
        <div class="profile-card">
          <h3>安全设置</h3>
          <div class="security-item">
            <div>
              <p class="security-label">密码</p>
              <p class="security-hint">定期修改密码保护账号安全</p>
            </div>
            <el-button @click="showPasswordDialog = true">修改密码</el-button>
          </div>
        </div>

        <!-- My posts link -->
        <div class="profile-card">
          <h3>我的帖子</h3>
          <el-button @click="$router.push('/profile/posts')">查看我的帖子</el-button>
        </div>
      </div>

      <!-- Change Password Dialog -->
      <el-dialog v-model="showPasswordDialog" title="修改密码" width="400px">
        <el-form :model="passwordForm" label-position="top">
          <el-form-item label="当前密码" :error="pwErrors.old">
            <el-input v-model="passwordForm.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" :error="pwErrors.new">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              show-password
              placeholder="至少 8 个字符"
            />
          </el-form-item>
          <el-form-item label="确认新密码" :error="pwErrors.confirm">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showPasswordDialog = false">取消</el-button>
          <el-button type="primary" :loading="changingPw" @click="handleChangePassword">
            确认
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { usersAPI } from '@/api/users'
import { authAPI } from '@/api/auth'
import { uploadAvatar } from '@/api/media'
import { validatePassword } from '@/utils/validation'
import UserAvatar from '@/components/common/UserAvatar.vue'
import AvatarCropDialog from '@/components/common/AvatarCropDialog.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'

const authStore = useAuthStore()
const user = ref(authStore.currentUser)
const loading = ref(false)
const error = ref<string | null>(null)
const updating = ref(false)
const changingPw = ref(false)
const showPasswordDialog = ref(false)

const userStats = reactive({
  post_count: 0,
  comment_count: 0,
  like_count: 0,
})

const profileForm = reactive({
  nickname: user.value?.nickname || '',
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const pwErrors = reactive({ old: '', new: '', confirm: '' })

const avatarInput = ref<HTMLInputElement | null>(null)
const uploadingAvatar = ref(false)
const showCropDialog = ref(false)
const cropImageSrc = ref('')

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

function handleAvatarChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    target.value = ''
    return
  }
  cropImageSrc.value = URL.createObjectURL(file)
  showCropDialog.value = true
  target.value = ''
}

async function handleCropConfirm(blob: Blob) {
  uploadingAvatar.value = true
  try {
    const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' })
    const res = await uploadAvatar(file)
    if (user.value) user.value.avatar_url = res.avatar_url
    ElMessage.success('头像更新成功')
  } catch {
    ElMessage.error('头像上传失败')
  } finally {
    uploadingAvatar.value = false
    URL.revokeObjectURL(cropImageSrc.value)
    cropImageSrc.value = ''
  }
}

async function loadStats() {
  if (!user.value?.id) return
  try {
    const data = await usersAPI.getUserStats()
    userStats.post_count = data.post_count
    userStats.comment_count = data.comment_count
    userStats.like_count = data.like_count
  } catch {
    /* silent */
  }
}

async function loadProfile() {
  loading.value = true
  error.value = null
  try {
    await authStore.fetchProfile()
    user.value = authStore.currentUser
    profileForm.nickname = user.value?.nickname || ''
    await loadStats()
  } catch {
    error.value = '加载用户信息失败'
  } finally {
    loading.value = false
  }
}

async function handleUpdateProfile() {
  updating.value = true
  try {
    await usersAPI.updateProfile({ nickname: profileForm.nickname || undefined })
    if (user.value) user.value.nickname = profileForm.nickname
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    updating.value = false
  }
}

async function handleChangePassword() {
  pwErrors.old = ''
  pwErrors.new = ''
  pwErrors.confirm = ''

  if (!passwordForm.old_password) {
    pwErrors.old = '请输入当前密码'
    return
  }
  const v = validatePassword(passwordForm.new_password)
  if (v !== true) {
    pwErrors.new = v
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    pwErrors.confirm = '两次输入的密码不一致'
    return
  }
  if (passwordForm.new_password === passwordForm.old_password) {
    pwErrors.new = '新密码不能与旧密码相同'
    return
  }

  changingPw.value = true
  try {
    await authAPI.resetPassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    showPasswordDialog.value = false
    await authStore.logout()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    const detail: string = e.response?.data?.detail || ''
    if (detail) {
      pwErrors.new = detail
    } else {
      ElMessage.error('密码修改失败')
    }
  } finally {
    changingPw.value = false
  }
}

onMounted(() => {
  if (!user.value) loadProfile()
  else loadStats()
})
</script>

<style scoped>
.profile-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}

.profile-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
}

.profile-card h3 {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border-light);
}

.profile-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg) 0;
}

.profile-avatar-section h2 {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.avatar-upload-wrapper {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
}

.avatar-upload-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: var(--font-size-xs);
  opacity: 0;
  transition: opacity 0.2s;
  border-radius: 50%;
}

.avatar-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 50%;
}

.profile-username {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.profile-stats {
  display: flex;
  justify-content: center;
  gap: var(--spacing-xl);
  padding-top: var(--spacing-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.security-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.security-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.security-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 2px;
}
</style>
