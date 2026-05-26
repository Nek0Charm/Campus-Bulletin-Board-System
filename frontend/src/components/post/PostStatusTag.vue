<template>
  <el-tag v-if="isPinned" type="danger" size="small" effect="dark">置顶</el-tag>
  <el-tag v-if="isFeatured" type="warning" size="small" effect="dark">加精</el-tag>
</template>

<script setup lang="ts">
defineProps<{
  isPinned: boolean
  isFeatured: boolean
}>()
</script>
