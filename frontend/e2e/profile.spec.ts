import { test, expect } from '@playwright/test'

test.describe('Profile', () => {
  test('can view own profile page', async ({ page }) => {
    await page.goto('/profile')
    await expect(page.locator('.el-breadcrumb__inner').filter({ hasText: '个人中心' })).toBeVisible(
      { timeout: 10000 },
    )
  })

  test('profile shows user information', async ({ page }) => {
    await page.goto('/profile')

    // Should show user stats
    await expect(page.getByText('帖子', { exact: true })).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('评论', { exact: true })).toBeVisible()
    await expect(page.getByText('获赞')).toBeVisible()
  })

  test('can update nickname', async ({ page }) => {
    await page.goto('/profile')

    await expect(page.getByText('编辑资料')).toBeVisible({ timeout: 10000 })

    const nicknameInput = page.getByPlaceholder('输入昵称')
    await nicknameInput.clear()
    await nicknameInput.fill('Updated E2E Nickname')

    await page.getByRole('button', { name: '保存' }).click()

    await expect(page.locator('.el-message').filter({ hasText: '成功' })).toBeVisible({
      timeout: 5000,
    })
  })

  test('can navigate to my posts', async ({ page }) => {
    await page.goto('/profile')

    await expect(page.getByRole('heading', { name: '我的帖子' })).toBeVisible({ timeout: 10000 })

    await page.getByRole('button', { name: '查看我的帖子' }).click()
    await expect(page).toHaveURL(/\/profile\/posts/, { timeout: 10000 })
  })

  test('can open change password dialog', async ({ page }) => {
    await page.goto('/profile')

    await expect(page.getByText('安全设置')).toBeVisible({ timeout: 10000 })

    await page.getByRole('button', { name: '修改密码' }).click()
    await expect(page.locator('.el-dialog').filter({ hasText: '修改密码' })).toBeVisible({
      timeout: 5000,
    })
  })
})
