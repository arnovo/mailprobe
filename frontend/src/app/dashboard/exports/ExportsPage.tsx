'use client';

/**
 * Exports page: request CSV export (POST /v1/exports/csv, returns job_id),
 * check status with GET /v1/jobs/{job_id} and download CSV when status === succeeded.
 */

import { useTranslations } from 'next-intl';
import { fetchWithAuth, getAccessToken } from '@/lib/auth';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function ExportsPage() {
  const t = useTranslations('exports');
  const tCommon = useTranslations('common');
  const tJobs = useTranslations('jobs');
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
      .catch(() => setError('Network error'))
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
        else setError(d.error?.message || 'Job not found');
      })
      .catch(() => setError('Network error'))
      .finally(() => setPolling(false));
  }

  function downloadCsv() {
    const csv = jobStatus?.result?.csv;
    if (!csv) return;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const dateStr = new Date().toISOString().split('T')[0];
    a.download = `leads-export-${dateStr}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!token) return <div className="card"><p>{tCommon('loading')}</p></div>;

  return (
    <div className="card">
      <h2>{t('title')}</h2>

      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <button type="button" onClick={requestExport} disabled={requesting}>
          {requesting ? tCommon('loading') : t('createCsv')}
        </button>
        {lastJobId && (
          <span style={{ color: '#94a3b8' }}>
            Last job: <code>{lastJobId}</code>
          </span>
        )}
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label htmlFor="export-job-id" style={{ display: 'block', marginBottom: '0.25rem' }}>Check job status</label>
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
            {polling ? tCommon('loading') : tCommon('search')}
          </button>
        </div>
      </div>

      {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}

      {jobStatus && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: '#0f172a', borderRadius: '0.5rem', border: '1px solid #334155' }}>
          <p><strong>{tCommon('status')}:</strong> {tJobs(`status.${jobStatus.status}` as never) || jobStatus.status}</p>
          <p><strong>Progress:</strong> {jobStatus.progress}%</p>
          {jobStatus.error && <p style={{ color: '#f87171' }}>{jobStatus.error}</p>}
          {jobStatus.status === 'succeeded' && jobStatus.result?.csv && (
            <p>
              Rows: {jobStatus.result.row_count ?? '—'}{' '}
              <button type="button" onClick={downloadCsv}>{t('download')}</button>
            </p>
          )}
        </div>
      )}

      {!jobStatus && !error && <p>{t('noExports')}</p>}
    </div>
  );
}
