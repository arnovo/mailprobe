/**
 * Auth: tokens en localStorage, refresh y fetch con Bearer.
 * Si la API devuelve 401, intenta refresh; si falla, limpia tokens y redirige a /login.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

export function clearAuthAndRedirect(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}

/**
 * Intenta renovar el access token con el refresh token.
 * Si OK: guarda nuevos tokens, dispara 'auth-token-updated' y devuelve el nuevo access_token.
 * Si falla: limpia y redirige a /login, devuelve null.
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) {
    clearAuthAndRedirect();
    return null;
  }
  try {
    const res = await fetch(`${API_URL}/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    const data = await res.json();
    if (data.error || !data.data?.access_token) {
      clearAuthAndRedirect();
      return null;
    }
    localStorage.setItem('access_token', data.data.access_token);
    if (data.data.refresh_token) {
      localStorage.setItem('refresh_token', data.data.refresh_token);
    }
    window.dispatchEvent(new CustomEvent('auth-token-updated'));
    return data.data.access_token;
  } catch {
    clearAuthAndRedirect();
    return null;
  }
}

/**
 * fetch con Authorization: Bearer y manejo de 401:
 * - Si la respuesta es 401, intenta refresh una vez y reintenta la misma petición.
 * - Si el refresh falla o la segunda petición sigue siendo 401, redirige a /login.
 * options puede incluir headers; se añade/sobrescribe Authorization.
 */
export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAccessToken();
  if (!token) {
    clearAuthAndRedirect();
    return Promise.reject(new Error('Not authenticated'));
  }
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${token}`);

  let res = await fetch(url, { ...options, headers });
  if (res.status !== 401) return res;

  const newToken = await refreshAccessToken();
  if (!newToken) return Promise.reject(new Error('Not authenticated'));

  headers.set('Authorization', `Bearer ${newToken}`);
  res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    clearAuthAndRedirect();
    return Promise.reject(new Error('Not authenticated'));
  }
  return res;
}
