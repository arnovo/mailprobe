import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  getAccessToken,
  getRefreshToken,
  clearAuthAndRedirect,
  fetchWithAuth,
  refreshAccessToken,
} from '@/lib/auth';

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';
const LOGIN_PATH = '/login';
const HTTP_OK = 200;
const EXPECTED_FETCH_CALLS_AFTER_REFRESH = 3;

describe('lib/auth', () => {
  let localStorageMock: Record<string, string>;
  let locationHref: string;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    localStorageMock = {};
    locationHref = '';
    fetchMock = vi.fn();

    vi.stubGlobal('localStorage', {
      getItem: (key: string) => localStorageMock[key] ?? null,
      setItem: (key: string, value: string) => {
        localStorageMock[key] = value;
      },
      removeItem: (key: string) => {
        delete localStorageMock[key];
      },
      clear: () => {
        localStorageMock = {};
      },
      length: 0,
      key: () => null,
    });

    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    });
    vi.spyOn(window.location, 'href', 'set').mockImplementation((v: string) => {
      locationHref = v;
    });
    Object.defineProperty(window, 'location', {
      value: {
        get href() {
          return locationHref;
        },
        set href(v: string) {
          locationHref = v;
        },
      },
      writable: true,
    });

    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe('getAccessToken', () => {
    it('returns null when no token is set', () => {
      expect(getAccessToken()).toBeNull();
    });

    it('returns the value when token is set', () => {
      const token = 'access-abc';
      localStorage.setItem(ACCESS_KEY, token);
      expect(getAccessToken()).toBe(token);
    });
  });

  describe('getRefreshToken', () => {
    it('returns null when no token is set', () => {
      expect(getRefreshToken()).toBeNull();
    });

    it('returns the value when token is set', () => {
      const token = 'refresh-xyz';
      localStorage.setItem(REFRESH_KEY, token);
      expect(getRefreshToken()).toBe(token);
    });
  });

  describe('clearAuthAndRedirect', () => {
    it('removes tokens and sets location.href to /login', () => {
      localStorage.setItem(ACCESS_KEY, 'a');
      localStorage.setItem(REFRESH_KEY, 'r');
      clearAuthAndRedirect();
      expect(localStorage.getItem(ACCESS_KEY)).toBeNull();
      expect(localStorage.getItem(REFRESH_KEY)).toBeNull();
      expect(window.location.href).toBe(LOGIN_PATH);
    });
  });

  describe('fetchWithAuth', () => {
    it('rejects when no token is set', async () => {
      await expect(fetchWithAuth('https://api.example/v1/leads')).rejects.toThrow(
        'Not authenticated'
      );
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it('resolves with response when token is set and status is 200', async () => {
      const token = 'bearer-token';
      localStorage.setItem(ACCESS_KEY, token);
      const mockRes = new Response('{}', { status: HTTP_OK });
      fetchMock.mockResolvedValue(mockRes);

      const res = await fetchWithAuth('https://api.example/v1/leads');
      expect(res).toBe(mockRes);
      expect(res.status).toBe(HTTP_OK);
      expect(fetchMock).toHaveBeenCalledWith(
        'https://api.example/v1/leads',
        expect.objectContaining({
          headers: expect.any(Headers),
        })
      );
      const callHeaders = fetchMock.mock.calls[0][1].headers as Headers;
      expect(callHeaders.get('Authorization')).toBe(`Bearer ${token}`);
    });

    it('retries with new token on 401 when refresh succeeds', async () => {
      const accessToken = 'old-access';
      const refreshToken = 'refresh-xyz';
      const newAccessToken = 'new-access';
      localStorage.setItem(ACCESS_KEY, accessToken);
      localStorage.setItem(REFRESH_KEY, refreshToken);

      const okRes = new Response('{}', { status: HTTP_OK });
      fetchMock
        .mockResolvedValueOnce(new Response('', { status: 401 }))
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({
              data: { access_token: newAccessToken },
            }),
            { status: HTTP_OK }
          )
        )
        .mockResolvedValueOnce(okRes);

      const res = await fetchWithAuth('https://api.example/v1/leads');
      expect(res.status).toBe(HTTP_OK);
      expect(fetchMock).toHaveBeenCalledTimes(EXPECTED_FETCH_CALLS_AFTER_REFRESH);
      expect(localStorage.getItem(ACCESS_KEY)).toBe(newAccessToken);
    });
  });

  describe('refreshAccessToken', () => {
    it('calls clearAuthAndRedirect and returns null when no refresh token', async () => {
      const result = await refreshAccessToken();
      expect(result).toBeNull();
      expect(window.location.href).toBe(LOGIN_PATH);
    });

    it('returns new access token and stores it when API succeeds', async () => {
      const refreshToken = 'refresh-xyz';
      const newAccessToken = 'new-access';
      localStorage.setItem(REFRESH_KEY, refreshToken);

      fetchMock.mockResolvedValue(
        new Response(
          JSON.stringify({
            data: { access_token: newAccessToken },
          }),
          { status: HTTP_OK }
        )
      );

      const result = await refreshAccessToken();
      expect(result).toBe(newAccessToken);
      expect(localStorage.getItem(ACCESS_KEY)).toBe(newAccessToken);
    });
  });
});
