export const DEFAULT_PAGE_SIZE = 20
export const PAGE_SIZE_OPTIONS = [10, 20, 50]

export const POST_STATUS_MAP: Record<string, { label: string; type: string }> = {
  normal: { label: '正常', type: '' },
  hidden: { label: '已隐藏', type: 'warning' },
  deleted: { label: '已删除', type: 'danger' },
}

export const USER_STATUS_MAP: Record<string, { label: string; type: string }> = {
  active: { label: '正常', type: 'success' },
  inactive: { label: '停用', type: 'info' },
  banned: { label: '封禁', type: 'danger' },
}

export const NOTIFICATION_TYPE_MAP: Record<string, string> = {
  comment: '评论了',
  reply: '回复了',
  like: '赞了',
  system: '系统通知',
}
