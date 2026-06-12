import { test, expect } from '@playwright/test'

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000/api/v1'

test.describe('Board - Home Page', () => {
  test('displays board section and latest posts on home page', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: '热门板块' })).toBeVisible({ timeout: 10000 })
    await expect(page.getByRole('heading', { name: '最新帖子' })).toBeVisible({ timeout: 5000 })
  })

  test('can navigate to boards list page', async ({ page }) => {
    await page.goto('/boards')
    await expect(page.getByRole('heading', { name: '版面列表' })).toBeVisible({ timeout: 10000 })
  })

  test('shows board cards when boards exist', async ({ page }) => {
    const boardsRes = await page.request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) {
      test.skip()
      return
    }

    await page.goto('/')
    // Board cards should be visible in the 热门板块 section
    await expect(page.locator('.board-card').first()).toBeVisible({ timeout: 5000 })
  })
})

test.describe('Board - Board Posts', () => {
  test('can navigate to a board page', async ({ page }) => {
    const boardsRes = await page.request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) {
      test.skip()
      return
    }

    const boardSlug = boards[0].slug
    await page.goto(`/boards/${boardSlug}`)

    // Breadcrumb should show the board name
    await expect(page.locator('.el-breadcrumb__inner').last()).toBeVisible({ timeout: 10000 })
  })

  test('board page shows post list or empty state', async ({ page }) => {
    const boardsRes = await page.request.get(`${API_BASE}/boards/`)
    const boardsData = await boardsRes.json()
    const boards = boardsData.data || boardsData

    if (!boards?.length) {
      test.skip()
      return
    }

    await page.goto(`/boards/${boards[0].slug}`)

    // Either posts or empty state should be visible
    await expect(
      page.locator('.post-list-item').first().or(page.getByText('暂无帖子')),
    ).toBeVisible({ timeout: 10000 })
  })
})
