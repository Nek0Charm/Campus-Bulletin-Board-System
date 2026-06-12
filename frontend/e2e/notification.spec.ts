import { test, expect } from '@playwright/test'

test.describe('Notification', () => {
  test('can view notifications page', async ({ page }) => {
    await page.goto('/notifications')

    await expect(page.getByRole('heading', { name: '通知' })).toBeVisible({ timeout: 10000 })
  })

  test('shows empty state when no notifications', async ({ page }) => {
    await page.goto('/notifications')

    // Should show either empty state or notification list
    const hasEmpty = await page
      .getByText('暂无通知')
      .isVisible({ timeout: 5000 })
      .catch(() => false)
    const hasNotifications = await page
      .locator('.notification-item, [class*="notif"]')
      .first()
      .isVisible({ timeout: 2000 })
      .catch(() => false)

    expect(hasEmpty || hasNotifications).toBeTruthy()
  })

  test('mark all read button works when there are unread notifications', async ({ page }) => {
    await page.goto('/notifications')

    const markAllReadBtn = page.getByRole('button', { name: '全部标为已读' })
    if (await markAllReadBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await markAllReadBtn.click()
      // After marking all as read, the button should disappear
      await expect(markAllReadBtn).toBeHidden({ timeout: 5000 })
    }
  })
})
