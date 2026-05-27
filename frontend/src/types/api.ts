export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  request_id?: string
}

export interface PaginatedData<T> {
  items: T[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface PaginatedResponse<T> {
  code: number
  message: string
  data: PaginatedData<T>
  request_id?: string
}

export interface ErrorResponse {
  code: number
  message: string
  errors?: { field: string; message: string }[]
  request_id?: string
}

export interface PageParams {
  page: number
  page_size: number
}
