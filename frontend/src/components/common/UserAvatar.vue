<template>
  <div class="user-avatar" :style="style">
    <img v-if="src" :src="src" :alt="name" />
    <span v-else class="avatar-text">{{ initial }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    src?: string
    name?: string
    size?: number
  }>(),
  {
    size: 36,
  },
)

const initial = computed(() => (props.name || '?').charAt(0).toUpperCase())
const style = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  fontSize: `${props.size * 0.45}px`,
}))
</script>

<style scoped>
.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-primary-light);
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-text {
  color: #fff;
  font-weight: 600;
  line-height: 1;
}
</style>
