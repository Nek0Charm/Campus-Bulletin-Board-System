<template>
  <div class="pagination-bar">
    <el-pagination
      v-model:current-page="currentPageModel"
      v-model:page-size="pageSizeModel"
      :page-sizes="pageSizeOptions"
      :total="total"
      layout="total, sizes, prev, pager, next"
      background
      @update:current-page="handlePageChange"
      @update:page-size="handleSizeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    currentPage: number
    pageSize: number
    total: number
    pageSizeOptions?: number[]
  }>(),
  {
    pageSizeOptions: () => [10, 20, 50],
  },
)

const emit = defineEmits<{
  'page-change': [page: number]
  'size-change': [size: number]
}>()

const currentPageModel = computed({
  get: () => props.currentPage,
  set: () => {},
})

const pageSizeModel = computed({
  get: () => props.pageSize,
  set: () => {},
})

function handlePageChange(page: number) {
  emit('page-change', page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleSizeChange(size: number) {
  emit('size-change', size)
}
</script>

<style scoped>
.pagination-bar {
  display: flex;
  justify-content: center;
  padding: var(--spacing-md) 0;
}
</style>
