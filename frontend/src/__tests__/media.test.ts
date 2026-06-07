import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getMediaUrl,
  uploadImage,
  getMediaInfo,
  deleteMedia,
  attachToPost,
  uploadAvatar,
} from '@/api/media'
import type {
  MediaUploadResponse,
  MediaRead,
  PostAttachmentRead,
  AvatarUploadResponse,
} from '@/types/media'

vi.mock('@/api/client', () => {
  const mockPost = vi.fn<() => Promise<unknown>>()
  const mockGet = vi.fn<() => Promise<unknown>>()
  const mockDelete = vi.fn<() => Promise<void>>()
  const mockPatch = vi.fn<() => Promise<unknown>>()
  return {
    default: {
      post: mockPost,
      get: mockGet,
      delete: mockDelete,
      patch: mockPatch,
    },
  }
})

import httpClient from '@/api/client'

const mockPost = vi.mocked(httpClient.post)
const mockGet = vi.mocked(httpClient.get)
const mockDelete = vi.mocked(httpClient.delete)
const mockPatch = vi.mocked(httpClient.patch)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('getMediaUrl', () => {
  it('returns correct URL for a given id', () => {
    const url = getMediaUrl('abc-123')
    expect(url).toBe('/api/v1/media/abc-123')
  })
})

describe('uploadImage', () => {
  const mockResponse: MediaUploadResponse = {
    id: 'media-uuid-1',
    url: '/api/v1/media/media-uuid-1',
    file_name: 'test.png',
    mime_type: 'image/png',
    file_size: 1024,
  }

  it('sends multipart form data with correct params', async () => {
    mockPost.mockResolvedValueOnce(mockResponse)
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    const result = await uploadImage(file, 'post')
    expect(mockPost).toHaveBeenCalledTimes(1)
    const callArgs = mockPost.mock.calls[0]
    expect((callArgs as [string])[0]).toContain('/api/v1/media/upload?source_type=post')
    expect(result).toEqual(mockResponse)
  })

  it('sends source_id when provided', async () => {
    mockPost.mockResolvedValueOnce(mockResponse)
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    await uploadImage(file, 'comment', 'post-uuid-1')
    const url = mockPost.mock.calls[0]![0] as string
    expect(url).toContain('source_type=comment')
    expect(url).toContain('source_id=post-uuid-1')
  })

  it('propagates errors from the API', async () => {
    mockPost.mockRejectedValueOnce(new Error('Upload failed'))
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    await expect(uploadImage(file)).rejects.toThrow('Upload failed')
  })
})

describe('getMediaInfo', () => {
  it('sends GET request to correct URL', async () => {
    const mockData: MediaRead = {
      id: 'media-1',
      uploader_id: 'user-1',
      url: '/api/v1/media/media-1',
      file_name: 'test.png',
      mime_type: 'image/png',
      file_size: 1024,
      source_type: 'post',
      is_public: true,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }
    mockGet.mockResolvedValueOnce(mockData)
    const result = await getMediaInfo('media-1')
    expect(mockGet).toHaveBeenCalledWith('/api/v1/media/media-1/info')
    expect(result).toEqual(mockData)
  })
})

describe('deleteMedia', () => {
  it('sends DELETE request to correct URL', async () => {
    mockDelete.mockResolvedValueOnce(undefined)
    await deleteMedia('media-1')
    expect(mockDelete).toHaveBeenCalledWith('/api/v1/media/media-1')
  })
})

describe('attachToPost', () => {
  const mockAttachments: PostAttachmentRead[] = [
    {
      id: 'att-1',
      post_id: 'post-1',
      media_id: 'media-1',
      sort_order: 0,
      created_at: '2025-01-01T00:00:00Z',
    },
  ]

  it('sends POST with media_ids', async () => {
    mockPost.mockResolvedValueOnce(mockAttachments)
    const result = await attachToPost('post-1', ['media-1'])
    expect(mockPost).toHaveBeenCalledWith('/api/v1/media/posts/post-1/attachments', {
      media_ids: ['media-1'],
    })
    expect(result).toEqual(mockAttachments)
  })
})

describe('uploadAvatar', () => {
  const mockResponse: AvatarUploadResponse = {
    avatar_url: '/api/v1/media/media-avatar-1',
  }

  it('sends PATCH with multipart form data', async () => {
    mockPatch.mockResolvedValueOnce(mockResponse)
    const file = new File(['test'], 'avatar.png', { type: 'image/png' })
    const result = await uploadAvatar(file)
    expect(mockPatch).toHaveBeenCalledTimes(1)
    const callArgs = mockPatch.mock.calls[0]
    expect((callArgs as [string])[0]).toBe('/api/v1/users/me/avatar')
    expect(result).toEqual(mockResponse)
  })
})
