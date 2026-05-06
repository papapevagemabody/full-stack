/**
 * Лаб. №5: модульные тесты утилит cookie (без сети).
 */
import {
  ACCESS_TOKEN_COOKIE,
  clearAuthCookies,
  getAccessTokenCookie,
  setAccessTokenCookie,
} from '../authCookies';

describe('authCookies', () => {
  beforeEach(() => {
    document.cookie.split(';').forEach((c) => {
      const eq = c.indexOf('=');
      const name = eq > -1 ? c.slice(0, eq).trim() : c.trim();
      if (name) {
        document.cookie = `${name}=; Path=/; Max-Age=0`;
      }
    });
  });

  it('setAccessTokenCookie / getAccessTokenCookie roundtrip', () => {
    expect(getAccessTokenCookie()).toBeNull();
    setAccessTokenCookie('abc.def.ghi');
    expect(getAccessTokenCookie()).toBe('abc.def.ghi');
    expect(document.cookie).toContain(ACCESS_TOKEN_COOKIE);
  });

  it('clearAuthCookies removes tokens', () => {
    setAccessTokenCookie('tok');
    clearAuthCookies();
    expect(getAccessTokenCookie()).toBeNull();
  });
});
