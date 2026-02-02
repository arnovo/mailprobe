'use client';

import { useEffect, useState } from 'react';
import { getAccessToken } from '@/lib/auth';

/**
 * Hook for authentication state management.
 * Handles token and workspace ID from localStorage.
 */
export function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  const [workspaceId, setWorkspaceId] = useState<string>('1');

  useEffect(() => {
    setToken(getAccessToken());
    const wid = typeof window !== 'undefined' ? localStorage.getItem('workspace_id') : null;
    if (wid) setWorkspaceId(wid);

    const onTokenUpdated = () => setToken(getAccessToken());
    window.addEventListener('auth-token-updated', onTokenUpdated);
    return () => window.removeEventListener('auth-token-updated', onTokenUpdated);
  }, []);

  const isAuthenticated = token !== null;

  return { token, workspaceId, isAuthenticated };
}
