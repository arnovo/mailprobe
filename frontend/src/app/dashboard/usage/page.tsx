'use client';

/**
 * Página Uso: GET /v1/usage para ver verificaciones usadas/límite, exports y plan del workspace.
 */

import { useEffect, useState } from 'react';
import { getAccessToken, fetchWithAuth } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function UsagePage() {
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
      .catch(() => setError('Error de red'))
      .finally(() => setLoading(false));
  }, [token, workspaceId]);

  if (!token) return <div className="card"><p>Cargando...</p></div>;

  return (
    <div className="card">
      <h2>Uso del workspace</h2>
      {loading ? <p>Cargando...</p> : error ? (
        <p style={{ color: '#f87171' }}>{error}</p>
      ) : data ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <p><strong>Plan:</strong> {data.plan ?? '—'}</p>
          <p><strong>Periodo:</strong> {data.period ?? '—'}</p>
          <p>
            <strong>Verificaciones:</strong> {data.verifications ?? 0} / {data.verifications_limit ?? '∞'}
          </p>
          <p><strong>Exports este periodo:</strong> {data.exports ?? 0}</p>
        </div>
      ) : (
        <p>No hay datos de uso.</p>
      )}
    </div>
  );
}
