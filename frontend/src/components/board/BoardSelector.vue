<template>
  <el-select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    placeholder="选择板块"
    filterable
  >
    <el-option v-for="board in boards" :key="board.id" :label="board.name" :value="board.id" />
  </el-select>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useBoardStore } from '@/stores/boards'

defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()

const boardStore = useBoardStore()

onMounted(() => {
  boardStore.fetchBoards()
})

const boards = boardStore.boards
</script>
