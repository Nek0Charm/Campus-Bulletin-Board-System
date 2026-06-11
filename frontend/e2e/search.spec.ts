import { test, expect } from '@playwright/test'

test.describe('Search', () => {
  test('search page loads correctly', async ({ page }) => {
    await page.goto('/search')
    await expect(page.getByText('搜索帖子')).toBeVisible({ timeout: 10000 })
    await expect(page.getByPlaceholder('搜索标题或正文')).toBeVisible()
  })

  test('can type a search query', async ({ page }) => {
    await page.goto('/search')
    const searchInput = page.getByPlaceholder('搜索标题或正文')
    await searchInput.fill('test query')
    await expect(searchInput).toHaveValue('test query')
  })

  test('shows empty state before searching', async ({ page }) => {
    await page.goto('/search')
    await expect(page.getByText('输入关键词开始搜索')).toBeVisible({ timeout: 5000 })
  })

  test('search with no results shows empty state', async ({ page }) => {
    await page.goto('/search')
    await page.getByPlaceholder('搜索标题或正文').fill('xyznonexistent12345query')
    await page.getByRole('button', { name: '搜索' }).click()

    await expect(page.getByText(/没有找到|暂无/)).toBeVisible({ timeout: 10000 })
  })

  test('search results update URL query params', async ({ page }) => {
    await page.goto('/search')
    await page.getByPlaceholder('搜索标题或正文').pressSequentially('test', { delay: 500 })
    await page.getByRole('button', { name: '搜索' }).click()

    await expect(page).toHaveURL(/q=test/, { timeout: 15000 })
  })
})
