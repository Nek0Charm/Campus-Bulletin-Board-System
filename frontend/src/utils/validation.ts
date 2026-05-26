export function validateUsername(value: string): string | true {
  if (!value.trim()) return '请输入用户名'
  if (value.length < 3) return '用户名至少 3 个字符'
  if (value.length > 32) return '用户名最多 32 个字符'
  return true
}

export function validateEmail(value: string): string | true {
  if (!value.trim()) return '请输入邮箱'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return '邮箱格式不正确'
  return true
}

export function validatePassword(value: string): string | true {
  if (!value) return '请输入密码'
  if (value.length < 8) return '密码至少 8 个字符'
  if (value.length > 128) return '密码最多 128 个字符'
  return true
}
