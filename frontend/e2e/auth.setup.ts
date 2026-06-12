import { test as setup, expect } from '@playwright/test'
import { apiRegister, apiVerifyEmail, apiLogin, apiGetProfile, buildStorageState } from './helpers'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'node:url'

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api/v1'
const __dirname = path.dirname(fileURLToPath(import.meta.url))
const AUTH_DIR = path.join(__dirname, '.auth')

function generateUser(prefix: string) {
  const suffix = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  return {
    username: `${prefix}_${suffix}`,
    email: `${prefix}_${suffix}@example.com`,
    password: 'Test1234!',
    nickname: `${prefix} User`,
  }
}

async function registerVerifyAndLogin(
  request: import('@playwright/test').APIRequestContext,
  user: { username: string; email: string; password: string; nickname?: string },
) {
  await apiRegister(request, user)
  await apiVerifyEmail(request, user.email)
  const token = await apiLogin(request, user.username, user.password)
  const profile = await apiGetProfile(request, token)
  return { token, profile }
}

setup('authenticate as regular user', async ({ request }) => {
  const user = generateUser('e2e_user')
  const { token, profile } = await registerVerifyAndLogin(request, user)
  const state = buildStorageState(token, profile.data)
  if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true })
  fs.writeFileSync(path.join(AUTH_DIR, 'user.json'), JSON.stringify(state, null, 2))
})

setup('authenticate as admin user', async ({ request }) => {
  const adminToken = process.env.E2E_ADMIN_TOKEN
  if (!adminToken) {
    // Skip admin setup gracefully — admin tests will fail but won't block other tests
    // Write a placeholder so the project dependency doesn't fail
    if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true })
    fs.writeFileSync(
      path.join(AUTH_DIR, 'admin.json'),
      JSON.stringify(
        buildStorageState('placeholder-token-needs-admin', { id: 'placeholder', role: 'admin' }),
        null,
        2,
      ),
    )
    setup.skip()
  }

  // Verify the admin token works and the user is admin
  const meRes = await request.get(`${API_BASE}/users/me`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  })
  expect(meRes.ok(), `Admin token is invalid or expired (status ${meRes.status()})`).toBeTruthy()
  const meData = await meRes.json()
  const userData = meData.data || meData
  expect(userData.role).toBe('admin')

  const state = buildStorageState(adminToken!, meData)
  if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true })
  fs.writeFileSync(path.join(AUTH_DIR, 'admin.json'), JSON.stringify(state, null, 2))
})
