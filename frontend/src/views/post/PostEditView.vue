<template>
  <div class="post-edit-page">
    <div class="content-container">
      <PageHeader
        :title="isEdit ? '编辑帖子' : '发布帖子'"
        :breadcrumbs="[
          { label: '首页', to: { name: 'Home' } },
          { label: isEdit ? '编辑帖子' : '发布帖子' },
        ]"
      />

      <LoadingSkeleton v-if="editLoading" type="detail" />
      <PostForm
        v-else
        :initial-data="initialData"
        :is-edit="isEdit"
        @submit="handleSubmit"
        @cancel="$router.back()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { usePostStore } from '@/stores/posts'
import PostForm from '@/components/post/PostForm.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import type { PostCreate } from '@/types/post'

const route = useRoute()
const router = useRouter()
const postStore = usePostStore()

const isEdit = computed(() => !!route.params.id)
const editLoading = ref(false)

const initialData = computed(() => {
  const post = postStore.currentPost
  if (isEdit.value && post) {
    return {
      title: post.title,
      content: post.content || '',
      board_id: post.board_id,
    }
  }
  if (!isEdit.value && route.query.board_id) {
    return {
      board_id: route.query.board_id as string,
    }
  }
  return undefined
})

async function handleSubmit(data: PostCreate) {
  try {
    if (isEdit.value) {
      await postStore.updatePost(route.params.id as string, data)
      ElMessage.success('已更新')
      router.push(`/posts/${route.params.id}`)
    } else {
      const newPost = await postStore.createPost(data)
      ElMessage.success('发布成功')
      router.push(`/posts/${newPost.id}`)
    }
  } catch {
    ElMessage.error(isEdit.value ? '更新失败' : '发布失败')
  }
}

onMounted(async () => {
  if (isEdit.value) {
    editLoading.value = true
    try {
      await postStore.fetchPostById(route.params.id as string)
    } catch {
      ElMessage.error('帖子不存在')
      router.push('/')
    } finally {
      editLoading.value = false
    }
  }
})
</script>

<style scoped>
.post-edit-page {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-lg) var(--spacing-md);
}
</style>
