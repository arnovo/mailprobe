'use client';

/**
 * Usage page: GET /v1/usage to see verifications used/limit, exports and workspace plan.
 */

import { fetchWithAuth, getAccessToken } from '@/lib/auth';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function UsagePage() {
  const t = useTranslations('usage');
  const tCommon = useTranslations('common');
  const [data, setData] = useState<{
    period?: string;
    verifications?: number;
    verifications_limit?: number;
    exports?: number;
    plan?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [token, setToken] = useState<string | null>(null);
  const [workspaceId, setWorkspaceId] = useState('1');

  useEffect(() => {
    setToken(getAccessToken());
    const wid = typeof window !== 'undefined' ? localStorage.getItem('workspace_id') : null;
    if (wid) setWorkspaceId(wid);
    const onTokenUpdated = () => setToken(getAccessToken());
    window.addEventListener('auth-token-updated', onTokenUpdated);
    return () => window.removeEventListener('auth-token-updated', onTokenUpdated);
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchWithAuth(`${API_URL}/v1/usage`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (d.data) setData(d.data);
        if (d.error) setError(d.error.message || 'Error');
      })
      .catch(() => setError('Network error'))
      .finally(() => setLoading(false));
  }, [token, workspaceId]);

  if (!token) return <div className="card"><p>{tCommon('loading')}</p></div>;

  return (
    <div className="card">
      <h2>{t('title')}</h2>
      {loading ? <p>{tCommon('loading')}</p> : error ? (
        <p style={{ color: '#f87171' }}>{error}</p>
      ) : data ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <p><strong>{t('currentPlan')}:</strong> {data.plan ?? '—'}</p>
          <p><strong>{t('resetDate')}:</strong> {data.period ?? '—'}</p>
          <p>
            <strong>{t('verificationsUsed')}:</strong> {data.verifications ?? 0} / {data.verifications_limit ?? '∞'}
          </p>
          <p><strong>Exports:</strong> {data.exports ?? 0}</p>
        </div>
      ) : (
        <p>No usage data.</p>
      )}
    </div>
  );
}
