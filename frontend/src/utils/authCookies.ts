/**
 * Токены в cookie, доступные из JS (без HttpOnly).
 * Важно: при XSS токен может быть украден — для продакшена часто предпочитают HttpOnly + same-site.
 */

export const ACCESS_TOKEN_COOKIE = 'access_token';
export const REFRESH_TOKEN_COOKIE = 'refresh_token';

/** Согласовано с backend/config.py по умолчанию */
const ACCESS_MAX_AGE_SEC = 30 * 60;
const REFRESH_MAX_AGE_SEC = 7 * 24 * 60 * 60;

function readAllCookies(): Record<string, string> {
  if (!document.cookie) return {};
  const out: Record<string, string> = {};
  for (const part of document.cookie.split(';')) {
    const idx = part.indexOf('=');
    if (idx === -1) continue;
    const k = part.slice(0, idx).trim();
    const v = part.slice(idx + 1).trim();
    try {
      out[k] = decodeURIComponent(v);
    } catch {
      out[k] = v;
    }
  }
  return out;
}

function buildCookieString(name: string, value: string, maxAgeSec: number): string {
  const enc = encodeURIComponent(value);
  const secure = typeof window !== 'undefined' && window.location.protocol === 'https:' ? '; Secure' : '';
  return `${name}=${enc}; Path=/; Max-Age=${maxAgeSec}; SameSite=Lax${secure}`;
}

export function getAccessTokenCookie(): string | null {
  const v = readAllCookies()[ACCESS_TOKEN_COOKIE];
  return v && v.length > 0 ? v : null;
}

export function getRefreshTokenCookie(): string | null {
  const v = readAllCookies()[REFRESH_TOKEN_COOKIE];
  return v && v.length > 0 ? v : null;
}

export function setAccessTokenCookie(token: string): void {
  document.cookie = buildCookieString(ACCESS_TOKEN_COOKIE, token, ACCESS_MAX_AGE_SEC);
}

export function setRefreshTokenCookie(token: string): void {
  document.cookie = buildCookieString(REFRESH_TOKEN_COOKIE, token, REFRESH_MAX_AGE_SEC);
}

export function clearAccessTokenCookie(): void {
  document.cookie = `${ACCESS_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function clearRefreshTokenCookie(): void {
  document.cookie = `${REFRESH_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function clearAuthCookies(): void {
  clearAccessTokenCookie();
  clearRefreshTokenCookie();
}

/** Однократный перенос со старого localStorage (если cookie ещё пусты). */
export function migrateTokensFromLocalStorage(): void {
  const oldAccess = localStorage.getItem('token');
  const oldRefresh = localStorage.getItem('refreshToken');
  if (oldAccess && !getAccessTokenCookie()) {
    setAccessTokenCookie(oldAccess);
    localStorage.removeItem('token');
  }
  if (oldRefresh && !getRefreshTokenCookie()) {
    setRefreshTokenCookie(oldRefresh);
    localStorage.removeItem('refreshToken');
  }
}
