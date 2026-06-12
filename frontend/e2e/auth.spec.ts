import { test, expect } from '@playwright/test'
import { apiRegister, apiVerifyEmail, uniqueSuffix } from './helpers'

test.describe('Auth - Registration & Login', () => {
  test('can navigate to login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: '校园论坛' })).toBeVisible({ timeout: 10000 })
  })

  test('can register a new user via the UI', async ({ page }) => {
    const suffix = uniqueSuffix()
    await page.goto('/login')

    await page.locator('.el-tabs__item', { hasText: '注册' }).click()

    await page.getByPlaceholder('3-32 个字符').fill(`e2e_reg_${suffix}`)
    await page.getByPlaceholder('请输入邮箱地址').fill(`e2e_reg_${suffix}@example.com`)
    await page.getByPlaceholder('可选').fill('E2E Registered')
    await page.getByPlaceholder('至少 8 个字符').first().fill('Test1234!')
    await page.getByPlaceholder('再次输入密码').fill('Test1234!')

    await page.getByRole('button', { name: '注 册' }).click()

    await expect(page).toHaveURL(/\/verify-email/, { timeout: 10000 })
  })

  test('can login with valid credentials', async ({ page, request }) => {
    const suffix = uniqueSuffix()
    const user = {
      username: `e2e_login_${suffix}`,
      email: `e2e_login_${suffix}@example.com`,
      password: 'Test1234!',
    }
    await apiRegister(request, user)
    await apiVerifyEmail(request, user.email)

    await page.goto('/login')
    await page.getByPlaceholder('用户名或邮箱').fill(user.username)
    await page.getByPlaceholder('请输入密码').fill(user.password)
    await page.getByRole('button', { name: '登 录' }).click()

    await expect(page).toHaveURL(/^(?!.*\/login)/, { timeout: 10000 })
  })

  test('shows error on wrong password', async ({ page, request }) => {
    const suffix = uniqueSuffix()
    const user = {
      username: `e2e_wrong_${suffix}`,
      email: `e2e_wrong_${suffix}@example.com`,
      password: 'Test1234!',
    }
    await apiRegister(request, user)
    await apiVerifyEmail(request, user.email)

    await page.goto('/login')
    await page.getByPlaceholder('用户名或邮箱').fill(user.username)
    await page.getByPlaceholder('请输入密码').fill('WrongPassword!')
    await page.getByRole('button', { name: '登 录' }).click()

    await expect(page.locator('.el-message').filter({ hasText: /错误|失败/ })).toBeVisible({
      timeout: 5000,
    })
  })

  test('unverified email shows verification dialog', async ({ page, request }) => {
    const suffix = uniqueSuffix()
    const user = {
      username: `e2e_unver_${suffix}`,
      email: `e2e_unver_${suffix}@example.com`,
      password: 'Test1234!',
    }
    await apiRegister(request, user)
    // intentionally skip email verification

    await page.goto('/login')
    await page.getByPlaceholder('用户名或邮箱').fill(user.username)
    await page.getByPlaceholder('请输入密码').fill(user.password)
    await page.getByRole('button', { name: '登 录' }).click()

    await expect(page.locator('.el-dialog').filter({ hasText: '邮箱未验证' })).toBeVisible({
      timeout: 10000,
    })
  })
})

test.describe('Auth - Route Guards', () => {
  test('redirects to login when not authenticated', async ({ page }) => {
    await page.goto('/profile')
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 })
  })

  test('login page shows link to register', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('立即注册')).toBeVisible({ timeout: 10000 })
  })

  test('register tab shows required fields', async ({ page }) => {
    await page.goto('/login')
    await page.locator('.el-tabs__item', { hasText: '注册' }).click()

    await expect(page.getByPlaceholder('3-32 个字符')).toBeVisible({ timeout: 5000 })
    await expect(page.getByPlaceholder('请输入邮箱地址')).toBeVisible()
    await expect(page.getByPlaceholder('至少 8 个字符').first()).toBeVisible()
  })
})
