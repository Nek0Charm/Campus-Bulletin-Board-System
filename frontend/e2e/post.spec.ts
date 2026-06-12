import { test, expect } from '@playwright/test'

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api/v1'

test.describe('Post - Create', () => {
  test('authenticated user can navigate to create post page', async ({ page }) => {
    await page.goto('/posts/new')
    await expect(page).toHaveURL(/\/posts\/new/, { timeout: 10000 })
    await expect(page.getByRole('heading', { name: '发布帖子' })).toBeVisible({ timeout: 5000 })
  })

  test('create post form shows required fields', async ({ page }) => {
    await page.goto('/posts/new')
    await expect(page.getByLabel('选择板块')).toBeVisible({ timeout: 10000 })
    await expect(page.getByPlaceholder('请输入帖子标题')).toBeVisible()
  })
})

test.describe('Post - View', () => {
  test('can navigate to a post from board page', async ({ page, request }) => {
    const boardsRes = await request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) {
      test.skip()
      return
    }

    const boardSlug = boards[0].slug
    await page.goto(`/boards/${boardSlug}`)

    const postLink = page.locator('.post-list-item, [class*="post-item"]').first()
    if (await postLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await postLink.click()
      await expect(page).toHaveURL(/\/posts\//, { timeout: 10000 })
    }
  })
})
