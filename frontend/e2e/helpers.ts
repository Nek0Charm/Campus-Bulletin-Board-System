import { APIRequestContext } from '@playwright/test'

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api/v1'
const MAILPIT_API = process.env.E2E_MAILPIT_API || 'http://localhost:8025/api/v1'

export function uniqueSuffix(): string {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

export async function apiRegister(
  request: APIRequestContext,
  user: { username: string; email: string; password: string; nickname?: string },
) {
  const res = await request.post(`${API_BASE}/auth/register`, { data: user })
  return res
}

export async function apiVerifyEmail(request: APIRequestContext, email: string) {
  // Poll Mailpit for the verification email (with retries)
  let msg: Record<string, unknown> | undefined
  for (let attempt = 0; attempt < 10; attempt++) {
    const messagesRes = await request.get(`${MAILPIT_API}/messages?limit=20`)
    const body = await messagesRes.json()
    const messages: Record<string, unknown>[] = body.messages ?? (Array.isArray(body) ? body : [])

    msg = messages.find((m) => {
      const toAddrs = (m.To as { Address: string }[]) ?? []
      return toAddrs.some((a) => a.Address.toLowerCase() === email.toLowerCase())
    })

    if (msg) break
    // Wait before retrying
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }

  if (!msg) throw new Error(`No verification email found for ${email}`)

  // Fetch full message to get the body
  const msgId = (msg as Record<string, unknown>).ID as string
  const fullMsgRes = await request.get(`${MAILPIT_API}/message/${msgId}`)
  const fullMsg = await fullMsgRes.json()
  const textBody = (fullMsg.Text as string) || (fullMsg.HTML as string) || ''

  // Extract token from verification URL: /verify-email?token=...
  const tokenMatch = textBody.match(/token=([^\s&"']+)/)
  if (!tokenMatch)
    throw new Error(
      'Could not extract verification token from email. Body: ' + textBody.slice(0, 200),
    )
  const token = tokenMatch[1]

  const verifyRes = await request.post(`${API_BASE}/auth/verify-email`, {
    data: { token },
  })
  if (!verifyRes.ok()) {
    const errBody = await verifyRes.text()
    throw new Error(`Email verification failed: ${verifyRes.status()} ${errBody}`)
  }
}

export async function apiLogin(request: APIRequestContext, account: string, password: string) {
  const res = await request.post(`${API_BASE}/auth/login`, {
    data: { account, password },
  })
  if (!res.ok()) {
    throw new Error(`Login failed for ${account}: ${res.status()}`)
  }
  const body = await res.json()
  return body.data.access_token as string
}

export async function apiCreateBoard(
  request: APIRequestContext,
  token: string,
  board: { name: string; slug: string; description?: string },
) {
  const res = await request.post(`${API_BASE}/admin/boards`, {
    data: board,
    headers: { Authorization: `Bearer ${token}` },
  })
  return res.json()
}

export async function apiCreatePost(
  request: APIRequestContext,
  token: string,
  post: { title: string; content: string; board_id?: string },
) {
  const res = await request.post(`${API_BASE}/posts/`, {
    data: post,
    headers: { Authorization: `Bearer ${token}` },
  })
  return res.json()
}

export async function apiCreateComment(
  request: APIRequestContext,
  token: string,
  postId: string,
  content: string,
) {
  const res = await request.post(`${API_BASE}/comments/?post_id=${postId}`, {
    data: { content },
    headers: { Authorization: `Bearer ${token}` },
  })
  return res.json()
}

export async function apiGetProfile(request: APIRequestContext, token: string) {
  const res = await request.get(`${API_BASE}/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return res.json()
}

export async function apiGetBoards(request: APIRequestContext) {
  const res = await request.get(`${API_BASE}/boards/`)
  return res.json()
}

export function buildStorageState(token: string, _user: Record<string, unknown>) {
  return {
    cookies: [],
    origins: [
      {
        origin: 'http://localhost:5173',
        localStorage: [{ name: 'bbs_token', value: token }],
      },
    ],
  }
}
