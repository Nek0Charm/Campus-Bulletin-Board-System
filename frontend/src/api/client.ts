import axios from 'axios'
import { getToken, removeToken } from '@/utils/storage'
import { ElMessage } from 'element-plus'

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

httpClient.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => Promise.reject(error),
)

httpClient.interceptors.response.use(
  (response) => {
    // 204 No Content has no body — resolve with undefined
    if (response.status === 204) {
      return undefined
    }
    const body = response.data
    if (body && body.code >= 200 && body.code < 300) {
      return body.data
    }
    return Promise.reject(body)
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      switch (status) {
        case 401:
          removeToken()
          break
        case 403:
          break
        case 404:
          break
        case 429:
          ElMessage.warning('操作过于频繁，请稍后重试')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        default:
          break
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  },
)

export default httpClient
