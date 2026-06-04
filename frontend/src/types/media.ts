export interface MediaUploadResponse {
  id: string
  url: string
  file_name: string
  mime_type: string
  file_size: number
  width?: number
  height?: number
}

export interface MediaRead {
  id: string
  uploader_id: string
  url: string
  file_name: string
  mime_type: string
  file_size: number
  width?: number
  height?: number
  source_type: string
  source_id?: string
  is_public: boolean
  created_at: string
  updated_at: string
}

export interface PostAttachmentRead {
  id: string
  post_id: string
  media_id: string
  sort_order: number
  created_at: string
}

export interface AvatarUploadResponse {
  avatar_url: string
}
