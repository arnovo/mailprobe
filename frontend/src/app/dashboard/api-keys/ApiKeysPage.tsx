'use client';

/**
 * API Keys page: list workspace keys, create (name + scopes) and revoke.
 * The full key is only returned once on creation; shown in a block to copy.
 */

import { fetchWithAuth, getAccessToken } from '@/lib/auth';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const SCOPES = ['leads:read', 'leads:write', 'verify:run', 'exports:run', 'optout:write', 'webhooks:write'];

type ApiKeyItem = {
  id: number;
  name: string;
  key_prefix: string;
  scopes: string[];
  rate_limit_per_minute: number;
  last_used_at: string | null;
  created_at: string;
  revoked_at: string | null;
};

export function ApiKeysPage() {
  const t = useTranslations('apiKeys');
  const tCommon = useTranslations('common');
  const [items, setItems] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newScopes, setNewScopes] = useState<string[]>(['leads:read', 'leads:write', 'verify:run']);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
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

  const load = useCallback(() => {
    if (!token) return;
    setLoading(true);
    fetchWithAuth(`${API_URL}/v1/api-keys`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.items) setItems(d.data.items);
        if (d.error) setError(d.error.message || 'Error');
      })
      .catch(() => setError('Network error'))
      .finally(() => setLoading(false));
  }, [token, workspaceId]);

  useEffect(() => {
    if (token) load();
  }, [token, load]);

  function toggleScope(s: string) {
    setNewScopes((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  }

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setCreating(true);
    fetchWithAuth(`${API_URL}/v1/api-keys`, {
      method: 'POST',
      headers: { 'X-Workspace-Id': workspaceId, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName || 'n8n', scopes: newScopes.length ? newScopes : SCOPES }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.key) {
          setCreatedKey(d.data.key);
          setNewName('');
          setNewScopes(['leads:read', 'leads:write', 'verify:run']);
          load();
        } else setError(d.error?.message || 'Error creating key');
      })
      .catch(() => setError('Network error'))
      .finally(() => setCreating(false));
  }

  function handleRevoke(id: number) {
    if (!confirm('Revoke this API key? You won\'t be able to use it again.')) return;
    fetchWithAuth(`${API_URL}/v1/api-keys/${id}`, {
      method: 'DELETE',
      headers: { 'X-Workspace-Id': workspaceId },
    })
      .then((r) => r.json())
      .then((d) => { if (!d.error) load(); else setError(d.error.message); })
      .catch(() => setError('Network error'));
  }

  function copyKey() {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey);
      alert(t('keyCopied'));
    }
  }

  if (!token) return <div className="card"><p>{tCommon('loading')}</p></div>;

  return (
    <div className="card">
      <h2>{t('title')}</h2>

      {createdKey && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: '#0f172a', borderRadius: '0.5rem', border: '1px solid #334155' }}>
          <p style={{ marginBottom: '0.5rem', fontWeight: 600 }}>{t('keyCopied')}:</p>
          <code style={{ wordBreak: 'break-all', display: 'block', marginBottom: '0.5rem' }}>{createdKey}</code>
          <button type="button" onClick={copyKey}>{t('copyKey')}</button>
          <button type="button" onClick={() => setCreatedKey(null)} style={{ marginLeft: '0.5rem' }}>{tCommon('close')}</button>
        </div>
      )}

      <form onSubmit={handleCreate} style={{ marginBottom: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' }}>
        <div>
          <label htmlFor="apikey-name" style={{ display: 'block', marginBottom: '0.25rem' }}>{t('name')}</label>
          <input
            id="apikey-name"
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="n8n / integration"
            style={{ width: 200 }}
          />
        </div>
        <div>
          <span id="apikey-scopes-label" style={{ display: 'block', marginBottom: '0.25rem' }}>{t('scopes')}</span>
          <div role="group" aria-labelledby="apikey-scopes-label" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {SCOPES.map((s) => (
              <label key={s} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <input type="checkbox" checked={newScopes.includes(s)} onChange={() => toggleScope(s)} />
                <span>{s}</span>
              </label>
            ))}
          </div>
        </div>
        <button type="submit" disabled={creating}>{creating ? tCommon('loading') : t('create')}</button>
      </form>

      {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}

      <h3 style={{ marginBottom: '0.5rem' }}>{t('title')}</h3>
      {loading ? <p>{tCommon('loading')}</p> : (
        <table>
          <thead>
            <tr>
              <th>{t('name')}</th>
              <th>{t('key')}</th>
              <th>{t('scopes')}</th>
              <th>{t('createdAt')}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.filter((k) => !k.revoked_at).map((k) => (
              <tr key={k.id}>
                <td>{k.name}</td>
                <td><code>{k.key_prefix}</code></td>
                <td>{k.scopes?.join(', ') || '-'}</td>
                <td>{k.created_at ? new Date(k.created_at).toLocaleString() : '-'}</td>
                <td>
                  <button type="button" onClick={() => handleRevoke(k.id)} style={{ color: '#f87171' }}>{t('revoke')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && items.filter((k) => !k.revoked_at).length === 0 && <p>{t('noKeys')}</p>}
    </div>
  );
}
