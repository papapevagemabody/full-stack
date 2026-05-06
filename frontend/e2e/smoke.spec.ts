import { test, expect } from '@playwright/test';

test.describe('E2E smoke (лаб. №5)', () => {
  test('главная: заголовок и навигация', async ({ page }) => {
    await page.goto('/');
    await expect(
      page.getByRole('heading', { level: 1, name: /Система цензурирования изображений/ })
    ).toBeVisible();
    // Две ссылки на /login: шапка («🔐 Войти») и блок гостя («Войти в систему») — strict mode требует однозначность
    await expect(page.getByRole('link', { name: '🔐 Войти' })).toBeVisible();
  });

  test('страница логина открывается', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /Вход в систему/ })).toBeVisible();
  });
});
