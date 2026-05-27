import httpClient from './client'
import type {
  LoginRequest,
  LoginData,
  RegisterRequest,
  VerifyEmailData,
  ResendVerifyRequest,
} from '@/types/user'

export const authAPI = {
  login(payload: LoginRequest): Promise<LoginData> {
    return httpClient.post('/api/v1/auth/login', payload)
  },

  register(payload: RegisterRequest): Promise<{ id: string; username: string }> {
    return httpClient.post('/api/v1/auth/register', payload)
  },

  logout(): Promise<void> {
    return httpClient.post('/api/v1/auth/logout')
  },

  resetPassword(payload: { old_password: string; new_password: string }): Promise<void> {
    return httpClient.post('/api/v1/auth/reset-password', payload)
  },

  verifyEmail(token: string): Promise<VerifyEmailData> {
    return httpClient.post('/api/v1/auth/verify-email', { token })
  },

  resendVerification(payload: ResendVerifyRequest): Promise<VerifyEmailData> {
    return httpClient.post('/api/v1/auth/resend-verification', payload)
  },
}
