import httpClient from './client'
import type { Board, BoardCreate, BoardUpdate } from '@/types/board'

export const boardsAPI = {
  getBoards(): Promise<Board[]> {
    return httpClient.get('/api/v1/boards/')
  },

  getBoard(slug: string): Promise<Board> {
    return httpClient.get(`/api/v1/boards/${slug}`)
  },

  createBoard(payload: BoardCreate): Promise<Board> {
    return httpClient.post('/api/v1/boards/', payload)
  },

  updateBoard(id: string, payload: BoardUpdate): Promise<Board> {
    return httpClient.patch(`/api/v1/boards/${id}`, payload)
  },

  deleteBoard(id: string): Promise<void> {
    return httpClient.delete(`/api/v1/boards/${id}`)
  },
}
