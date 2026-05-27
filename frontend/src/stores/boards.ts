import { defineStore } from 'pinia'
import { ref } from 'vue'
import { boardsAPI } from '@/api/boards'
import type { Board } from '@/types/board'

export const useBoardStore = defineStore('boards', () => {
  const boards = ref<Board[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchBoards() {
    if (boards.value.length > 0) return
    loading.value = true
    error.value = null
    try {
      boards.value = await boardsAPI.getBoards()
    } catch {
      error.value = '加载板块失败'
    } finally {
      loading.value = false
    }
  }

  return { boards, loading, error, fetchBoards }
})
