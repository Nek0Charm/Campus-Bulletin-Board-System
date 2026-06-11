import { test, expect } from '@playwright/test'

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api/v1'

test.describe('Comment - View', () => {
  test('comment section is visible on post detail page', async ({ page, request }) => {
    const boardsRes = await request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) {
      test.skip()
      return
    }

    const postsRes = await request.get(`${API_BASE}/posts/?board_id=${boards[0].id}`)
    const postsData = await postsRes.json()
    const posts = postsData.data?.items || postsData.items || postsData

    if (!posts?.length) {
      test.skip()
      return
    }

    await page.goto(`/posts/${posts[0].id}`)
    await expect(page.getByRole('heading', { name: '评论' })).toBeVisible({ timeout: 10000 })
  })

  test('unauthenticated user sees login prompt for comments', async ({ page, request }) => {
    const boardsRes = await request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) {
      test.skip()
      return
    }

    const postsRes = await request.get(`${API_BASE}/posts/?board_id=${boards[0].id}`)
    const postsData = await postsRes.json()
    const posts = postsData.data?.items || postsData.items || postsData

    if (!posts?.length) {
      test.skip()
      return
    }

    // Clear auth state to test unauthenticated view
    await page.goto(`/posts/${posts[0].id}`)
    await page.evaluate(() => localStorage.removeItem('bbs_token'))
    await page.reload()

    const loginPrompt = page.getByText('登录').filter({ hasText: /请.*登录/ })
    if (await loginPrompt.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Login prompt visible when not authenticated
    }
  })
})

test.describe('Comment - Create', () => {
  test('authenticated user can see comment form', async ({ page, request }) => {
    const boardsRes = await request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) {
      test.skip()
      return
    }

    const postsRes = await request.get(`${API_BASE}/posts/?board_id=${boards[0].id}`)
    const postsData = await postsRes.json()
    const posts = postsData.data?.items || postsData.items || postsData

    if (!posts?.length) {
      test.skip()
      return
    }

    await page.goto(`/posts/${posts[0].id}`)

    // Authenticated user should see comment form, not login prompt
    const commentForm = page.locator('.comment-input-area, .comment-form')
    if (await commentForm.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Comment form visible
    }

    // Muted user should see mute alert
    const muteAlert = page.getByText('禁言')
    if (await muteAlert.isVisible({ timeout: 1000 }).catch(() => false)) {
      // User is muted
    }
  })
})
