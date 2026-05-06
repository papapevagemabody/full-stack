/**
 * Публичный URL сайта для canonical и JSON-LD.
 * В продакшене задайте REACT_APP_PUBLIC_SITE_URL=https://ваш-домен.ru
 */
export function getPublicSiteUrl(): string {
  const env = process.env.REACT_APP_PUBLIC_SITE_URL;
  if (env != null && String(env).trim() !== '') {
    return String(env).trim().replace(/\/$/, '');
  }
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  return 'http://localhost:3000';
}
