'use client';

import { useCallback, useEffect, useState } from 'react';
import { fetchWithAuth } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Job {
  job_id: string;
  kind: string;
  status: string;
  progress: number;
  lead_id: number | null;
  created_at: string | null;
}

interface UseJobsOptions {
  token: string | null;
  workspaceId: string;
  activeOnly?: boolean;
}

export function useJobs({ token, workspaceId, activeOnly = true }: UseJobsOptions) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const loadJobs = useCallback(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    const q = activeOnly ? '?active_only=true' : '';
    fetchWithAuth(`${API_URL}/v1/jobs${q}`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.jobs) setJobs(d.data.jobs);
        if (d.error) setError(d.error.message || 'errors.loadJobs');
      })
      .catch(() => setError('Error de red'))
      .finally(() => setLoading(false));
  }, [token, workspaceId, activeOnly]);

  useEffect(() => {
    if (token) loadJobs();
  }, [token, loadJobs]);

  const cancelJob = useCallback((jobId: string) => {
    setCancellingId(jobId);
    setCancelError(null);
    fetchWithAuth(`${API_URL}/v1/jobs/${jobId}/cancel`, {
      method: 'POST',
      headers: { 'X-Workspace-Id': workspaceId },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.error) {
          let msg = d.error.message || 'errors.cancelFailed';
          if (d.error.code === 'JOB_INVALID_STATE' || (typeof msg === 'string' && msg.toLowerCase().includes('superadmin'))) {
            msg = 'errors.cancelFailed';
          }
          setCancelError(msg);
        } else {
          loadJobs();
        }
      })
      .catch(() => setCancelError('errors.networkError'))
      .finally(() => setCancellingId(null));
  }, [workspaceId, loadJobs]);

  return { jobs, loading, error, cancellingId, cancelError, cancelJob, reload: loadJobs };
}
