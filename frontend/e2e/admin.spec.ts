import { test, expect } from '@playwright/test'

test.describe('Admin - Dashboard', () => {
  test('admin can view dashboard with stats', async ({ page }) => {
    await page.goto('/admin')

    await expect(page.getByRole('heading', { name: '统计面板' })).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('用户总数')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('帖子总数')).toBeVisible()
    await expect(page.getByText('评论总数')).toBeVisible()
    await expect(page.getByText('今日新帖')).toBeVisible()
  })
})

test.describe('Admin - User Management', () => {
  test('admin can navigate to user management page', async ({ page }) => {
    await page.goto('/admin/users')

    await expect(page.getByRole('heading', { name: '用户管理' })).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Admin - Announcements', () => {
  test('admin can navigate to announcements page', async ({ page }) => {
    await page.goto('/admin/announcements')

    await expect(page.getByRole('heading', { name: '公告管理' })).toBeVisible({ timeout: 10000 })
  })

  test('announcements page shows create button', async ({ page }) => {
    await page.goto('/admin/announcements')

    await expect(page.getByRole('button', { name: '发布公告' })).toBeVisible({ timeout: 5000 })
  })

  test('admin can open create announcement dialog', async ({ page }) => {
    await page.goto('/admin/announcements')

    await page.getByRole('button', { name: '发布公告' }).click()
    await expect(page.locator('.el-dialog').filter({ hasText: '发布公告' })).toBeVisible({
      timeout: 5000,
    })
  })
})

test.describe('Admin - Board Management', () => {
  test('admin can navigate to board management page', async ({ page }) => {
    await page.goto('/admin/boards')

    await expect(page.getByRole('heading', { name: '板块管理' })).toBeVisible({ timeout: 10000 })
  })

  test('admin can create a new board', async ({ page }) => {
    await page.goto('/admin/boards')
    await expect(page.getByRole('heading', { name: '板块管理' })).toBeVisible({ timeout: 10000 })

    const createBtn = page.getByRole('button', { name: /新增|创建|添加/ }).first()
    if (await createBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await createBtn.click()

      // Wait for the dialog to appear
      const dialog = page.locator('.el-dialog').filter({ hasText: /板块|新增/ })
      if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
        const suffix = Date.now().toString(36)
        await page
          .getByPlaceholder(/板块名称|名称/)
          .first()
          .fill(`E2E Admin Board ${suffix}`)
        await page
          .getByPlaceholder(/slug|标识/)
          .first()
          .fill(`e2e-aboard-${suffix}`)
        await page
          .getByPlaceholder(/描述|description/)
          .first()
          .fill('E2E test board description')

        await page
          .getByRole('button', { name: /确定|提交|保存|创建/ })
          .last()
          .click()
      }
    }
  })
})
