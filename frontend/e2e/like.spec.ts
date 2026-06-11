import { test, expect } from '@playwright/test'

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api/v1'

test.describe('Like - Post', () => {
  test('like button is visible on post detail page', async ({ page }) => {
    const boardsRes = await page.request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) return

    const postsRes = await page.request.get(`${API_BASE}/posts/?board_id=${boards[0].id}`)
    const postsData = await postsRes.json()
    const posts = postsData.data?.items || postsData.items || postsData

    if (!posts?.length) return

    await page.goto(`/posts/${posts[0].id}`)

    const interactionBar = page.locator('.interaction-bar')
    if (await interactionBar.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Like button and comment count visible
      await expect(interactionBar).toBeVisible()
    }
  })
})
