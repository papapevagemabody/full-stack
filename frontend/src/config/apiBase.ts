/**
 * Базовый URL API.
 * Если REACT_APP_API_URL не задан — пустая строка: в dev запросы идут на тот же origin
 * и перенаправляются через "proxy" в package.json на backend.
 * Для прямого обращения к порту укажите, например: REACT_APP_API_URL=http://localhost:8001
 */
export function getApiBase(): string {
  const raw = process.env.REACT_APP_API_URL;
  if (raw == null || String(raw).trim() === '') {
    return '';
  }
  return String(raw).trim().replace(/\/$/, '');
}
