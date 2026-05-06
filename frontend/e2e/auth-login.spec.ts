import { test, expect } from '@playwright/test';

/**
 * Требует запущенный backend (прокси CRA → 8001) и учётную запись.
 * Пример: E2E_ADMIN_USER=admin E2E_ADMIN_PASSWORD=secret123 npm run test:e2e
 */
test.describe('E2E вход (лаб. №5)', () => {
  test('логин администратора и выход', async ({ page }) => {
    const user = process.env.E2E_ADMIN_USER;
    const pass = process.env.E2E_ADMIN_PASSWORD;
    test.skip(!user || !pass, 'Задайте E2E_ADMIN_USER и E2E_ADMIN_PASSWORD');
    const backendOk = await page.request
      .get('http://127.0.0.1:8001/health', { timeout: 4000 })
      .then((r) => r.ok())
      .catch(() => false);
    test.skip(!backendOk, 'Backend недоступен: запустите FastAPI на 127.0.0.1:8001');

    await page.goto('/login');
    await page.getByLabel(/Имя пользователя/i).fill(user!);
    await page.getByLabel(/Пароль/i).fill(pass!);
    await page.getByRole('button', { name: /войти/i }).click();

    // Успешный вход подтверждаем по кнопке "Выйти" в шапке.
    // URL в dev может обновляться не мгновенно, поэтому опираемся на UI-признак авторизации.
    const logoutButton = page.getByRole('button', { name: /выйти/i });
    try {
      await expect(logoutButton).toBeVisible({ timeout: 30_000 });
    } catch (e) {
      const errorText = await page.locator('.error-message').first().textContent().catch(() => null);
      throw new Error(`Логин не подтверждён в UI. Сообщение формы: ${errorText ?? 'нет'}`);
    }
    await logoutButton.click();
    await expect(page.getByRole('link', { name: '🔐 Войти' })).toBeVisible();
  });
});
