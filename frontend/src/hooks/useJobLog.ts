'use client';

import { fetchWithAuth } from '@/lib/auth';
import type { LogEntry } from '@/types';
import { useCallback, useEffect, useRef, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const POLL_INTERVAL = 2500;
const TERMINAL_STATUSES = ['succeeded', 'failed', 'cancelled'];

export interface UseJobLogState {
  lines: string[];
  entries: LogEntry[];
  status: string | null;
  loading: boolean;
  error: string | null;
  cleanup: () => void;
  refetch: () => void;
}

/**
 * Hook genérico para obtener y hacer polling del log de un job.
 * Se usa tanto para jobs directos como para logs de leads.
 */
export function useJobLog(jobId: string | null, workspaceId: string): UseJobLogState {
  const [lines, setLines] = useState<string[]>([]);
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const fetchLog = useCallback((showLoading: boolean) => {
    if (!jobId) return;
    if (showLoading) setLoading(true);
    
    fetchWithAuth(`${API_URL}/v1/jobs/${jobId}`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (showLoading) setLoading(false);
        if (d.error) {
          if (showLoading) setError(d.error.message || 'errors.jobFailed');
          return;
        }
        setEntries(Array.isArray(d.data?.log_entries) ? d.data.log_entries : []);
        setLines(Array.isArray(d.data?.log_lines) ? d.data.log_lines : []);
        const st = d.data?.status ?? null;
        setStatus(st);
        // Stop polling when job is in terminal state
        if (TERMINAL_STATUSES.includes(st)) {
          stopPolling();
        }
      })
      .catch(() => {
        if (showLoading) {
          setLoading(false);
          setError('Error de red');
        }
      });
  }, [jobId, workspaceId, stopPolling]);

  const reset = useCallback(() => {
    setLines([]);
    setEntries([]);
    setStatus(null);
    setError(null);
  }, []);

  // Initial fetch when jobId changes
  useEffect(() => {
    if (!jobId) return;
    reset();
    fetchLog(true);
  }, [jobId, fetchLog, reset]);

  // Polling
  useEffect(() => {
    if (!jobId) return;
    const interval = setInterval(() => fetchLog(false), POLL_INTERVAL);
    pollRef.current = interval;
    return stopPolling;
  }, [jobId, fetchLog, stopPolling]);

  return {
    lines,
    entries,
    status,
    loading,
    error,
    cleanup: stopPolling,
    refetch: () => fetchLog(true),
  };
}
