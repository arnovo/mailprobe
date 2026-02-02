'use client';

/**
 * Página Exports: solicitar exportación CSV (POST /v1/exports/csv, devuelve job_id),
 * consultar estado con GET /v1/jobs/{job_id} y descargar CSV cuando status === succeeded.
 */

import { fetchWithAuth, getAccessToken } from '@/lib/auth';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ExportsPage() {
  const [jobId, setJobId] = useState('');
  const [requesting, setRequesting] = useState(false);
  const [lastJobId, setLastJobId] = useState('');
  const [pollJobId, setPollJobId] = useState('');
  const [jobStatus, setJobStatus] = useState<{ status: string; progress: number; result?: { csv?: string; row_count?: number }; error?: string } | null>(null);
  const [polling, setPolling] = useState(false);
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

  function requestExport() {
    setError('');
    setRequesting(true);
    fetchWithAuth(`${API_URL}/v1/exports/csv`, {
      method: 'POST',
      headers: { 'X-Workspace-Id': workspaceId },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.job_id) {
          setLastJobId(d.data.job_id);
          setPollJobId(d.data.job_id);
          setJobStatus(null);
        } else setError(d.error?.message || 'Error');
      })
      .catch(() => setError('Error de red'))
      .finally(() => setRequesting(false));
  }

  function checkJob(id: string) {
    if (!id.trim()) return;
    setError('');
    setJobStatus(null);
    setPolling(true);
    fetchWithAuth(`${API_URL}/v1/jobs/${id.trim()}`, {
      headers: { 'X-Workspace-Id': workspaceId },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.data) setJobStatus(d.data);
        else setError(d.error?.message || 'Job no encontrado');
      })
      .catch(() => setError('Error de red'))
      .finally(() => setPolling(false));
  }

  function downloadCsv() {
    const csv = jobStatus?.result?.csv;
    if (!csv) return;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads-export-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!token) return <div className="card"><p>Cargando...</p></div>;

  return (
    <div className="card">
      <h2>Exportar CSV</h2>
      <p style={{ marginBottom: '1rem', color: '#94a3b8' }}>
        Genera un CSV con los leads del workspace (excluyendo opt-out). La exportación es asíncrona: solicita y luego consulta el estado por job_id.
      </p>

      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <button type="button" onClick={requestExport} disabled={requesting}>
          {requesting ? 'Solicitando...' : 'Solicitar exportación CSV'}
        </button>
        {lastJobId && (
          <span style={{ color: '#94a3b8' }}>
            Último job: <code>{lastJobId}</code>
          </span>
        )}
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label htmlFor="export-job-id" style={{ display: 'block', marginBottom: '0.25rem' }}>Consultar estado de un job</label>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            id="export-job-id"
            type="text"
            value={pollJobId || jobId}
            onChange={(e) => { setPollJobId(e.target.value); setJobId(e.target.value); }}
            placeholder="job_id (UUID)"
            style={{ flex: 1, maxWidth: 320 }}
          />
          <button type="button" onClick={() => checkJob(pollJobId || jobId)} disabled={polling}>
            {polling ? 'Consultando...' : 'Consultar'}
          </button>
        </div>
      </div>

      {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}

      {jobStatus && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: '#0f172a', borderRadius: '0.5rem', border: '1px solid #334155' }}>
          <p><strong>Estado:</strong> {jobStatus.status}</p>
          <p><strong>Progreso:</strong> {jobStatus.progress}%</p>
          {jobStatus.error && <p style={{ color: '#f87171' }}>{jobStatus.error}</p>}
          {jobStatus.status === 'succeeded' && jobStatus.result?.csv && (
            <p>
              Filas: {jobStatus.result.row_count ?? '—'}{' '}
              <button type="button" onClick={downloadCsv}>Descargar CSV</button>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
