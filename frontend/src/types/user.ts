export type UserRole = 'user' | 'admin'
export type UserStatus = 'active' | 'inactive' | 'banned'

export interface User {
  id: string
  username: string
  email: string
  nickname?: string
  avatar_url?: string
  role: UserRole
  status: UserStatus
  last_login_at?: string
  created_at: string
  updated_at: string
}

export interface AuthorInfo {
  id: string
  username: string
  nickname?: string
  avatar_url?: string
}

export interface LoginRequest {
  account: string
  password: string
}

export interface LoginData {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthorInfo
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  nickname?: string
}

export interface ResetPasswordRequest {
  old_password: string
  new_password: string
}

export interface VerifyEmailData {
  message: string
}

export interface ResendVerifyRequest {
  email: string
}
