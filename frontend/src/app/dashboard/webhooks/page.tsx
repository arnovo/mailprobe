'use client';

/**
 * Página Webhooks: listar webhooks del workspace y crear uno (URL + eventos).
 * POST /v1/webhooks devuelve el secret para firmar; no se vuelve a mostrar.
 */

import { fetchWithAuth, getAccessToken } from '@/lib/auth';
import { useCallback, useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const EVENT_OPTIONS = ['lead.created', 'verification.completed', 'export.completed', 'optout.recorded'];

type WebhookItem = {
  id: number;
  url: string;
  events: string[];
  is_active: boolean;
  created_at: string;
};

export default function WebhooksPage() {
  const [items, setItems] = useState<WebhookItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [newEvents, setNewEvents] = useState<string[]>(['lead.created', 'verification.completed']);
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
    fetchWithAuth(`${API_URL}/v1/webhooks`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.items) setItems(d.data.items);
        if (d.error) setError(d.error.message || 'Error');
      })
      .catch(() => setError('Error de red'))
      .finally(() => setLoading(false));
  }, [token, workspaceId]);

  useEffect(() => {
    if (token) load();
  }, [token, load]);

  function toggleEvent(ev: string) {
    setNewEvents((prev) => (prev.includes(ev) ? prev.filter((x) => x !== ev) : [...prev, ev]));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!newUrl.trim()) {
      setError('Indica la URL del webhook');
      return;
    }
    setError('');
    setSubmitting(true);
    fetchWithAuth(`${API_URL}/v1/webhooks`, {
      method: 'POST',
      headers: { 'X-Workspace-Id': workspaceId, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: newUrl.trim(),
        events: newEvents.length ? newEvents : EVENT_OPTIONS,
      }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.id) {
          setNewUrl('');
          setNewEvents(['lead.created', 'verification.completed']);
          load();
        } else setError(d.error?.message || 'Error al crear');
      })
      .catch(() => setError('Error de red'))
      .finally(() => setSubmitting(false));
  }

  if (!token) return <div className="card"><p>Cargando...</p></div>;

  return (
    <div className="card">
      <h2>Webhooks</h2>
      <p style={{ marginBottom: '1rem', color: '#94a3b8' }}>
        Recibe eventos (leads, verificaciones, exports) en tu URL. La respuesta incluye un secret para firmar peticiones.
      </p>

      <form onSubmit={handleSubmit} style={{ marginBottom: '1.5rem' }}>
        <div style={{ marginBottom: '0.75rem' }}>
          <label htmlFor="webhook-url" style={{ display: 'block', marginBottom: '0.25rem' }}>URL</label>
          <input
            id="webhook-url"
            type="url"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="https://tu-servidor.com/webhook"
            style={{ width: '100%', maxWidth: 400 }}
          />
        </div>
        <div style={{ marginBottom: '0.75rem' }}>
          <span id="webhook-events-label" style={{ display: 'block', marginBottom: '0.25rem' }}>Eventos</span>
          <div role="group" aria-labelledby="webhook-events-label" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {EVENT_OPTIONS.map((ev) => (
              <label key={ev} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <input type="checkbox" checked={newEvents.includes(ev)} onChange={() => toggleEvent(ev)} />
                <span>{ev}</span>
              </label>
            ))}
          </div>
        </div>
        <button type="submit" disabled={submitting}>{submitting ? 'Guardando...' : 'Añadir webhook'}</button>
      </form>

      {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}

      <h3 style={{ marginBottom: '0.5rem' }}>Webhooks registrados</h3>
      {loading ? <p>Cargando...</p> : (
        <table>
          <thead>
            <tr>
              <th>URL</th>
              <th>Eventos</th>
              <th>Activo</th>
              <th>Creado</th>
            </tr>
          </thead>
          <tbody>
            {items.map((w) => (
              <tr key={w.id}>
                <td><code style={{ fontSize: '0.875rem' }}>{w.url}</code></td>
                <td>{w.events?.join(', ') || '-'}</td>
                <td>{w.is_active ? 'Sí' : 'No'}</td>
                <td>{w.created_at ? new Date(w.created_at).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && items.length === 0 && <p>No hay webhooks. Añade uno arriba.</p>}
    </div>
  );
}
