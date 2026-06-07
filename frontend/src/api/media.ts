import httpClient from './client'
import type {
  MediaUploadResponse,
  MediaRead,
  PostAttachmentRead,
  AvatarUploadResponse,
} from '@/types/media'

export function getMediaUrl(id: string): string {
  return `/api/v1/media/${id}`
}

export async function uploadImage(
  file: File,
  sourceType: string = 'post',
  sourceId?: string,
): Promise<MediaUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const params = new URLSearchParams()
  params.append('source_type', sourceType)
  if (sourceId) params.append('source_id', sourceId)
  return httpClient.post(
    `/api/v1/media/upload?${params.toString()}`,
    formData,
  ) as Promise<MediaUploadResponse>
}

export async function getMediaInfo(id: string): Promise<MediaRead> {
  return httpClient.get(`/api/v1/media/${id}/info`) as Promise<MediaRead>
}

export async function deleteMedia(id: string): Promise<void> {
  await httpClient.delete(`/api/v1/media/${id}`)
}

export async function attachToPost(
  postId: string,
  mediaIds: string[],
): Promise<PostAttachmentRead[]> {
  return httpClient.post(`/api/v1/media/posts/${postId}/attachments`, {
    media_ids: mediaIds,
  }) as Promise<PostAttachmentRead[]>
}

export async function uploadAvatar(file: File): Promise<AvatarUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return httpClient.patch('/api/v1/users/me/avatar', formData) as Promise<AvatarUploadResponse>
}
