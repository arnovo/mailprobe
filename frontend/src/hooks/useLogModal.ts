'use client';

import { fetchWithAuth } from '@/lib/auth';
import type { LogEntry } from '@/types';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useJobLog } from './useJobLog';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Job {
  job_id: string;
  status: string;
  created_at: string | null;
}

export interface UseLogModalState {
  lines: string[];
  entries: LogEntry[];
  status: string | null;
  loading: boolean;
  error: string | null;
  jobId: string | null;
  jobs: Job[];
  jobIndex: number;
  cancelling: boolean;
  navigate: (direction: 'prev' | 'next') => void;
  handleCancel: () => void;
  cleanup: () => void;
}

/**
 * Hook para el modal de log de un lead.
 * Obtiene el último job del lead y permite navegar entre jobs históricos.
 */
export function useLogModal(lead: { id: number } | null, workspaceId: string): UseLogModalState {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobIndex, setJobIndex] = useState(0);
  const [cancelling, setCancelling] = useState(false);
  const [initialLoading, setInitialLoading] = useState(false);
  const [initialError, setInitialError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Reutilizamos useJobLog para el fetch del job actual
  const jobLog = useJobLog(currentJobId, workspaceId);

  const fetchLeadLog = useCallback((leadId: number) => {
    setInitialLoading(true);
    fetchWithAuth(`${API_URL}/v1/leads/${leadId}/verification-log`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        setInitialLoading(false);
        if (d.error) {
          setInitialError(d.error.message || 'No hay log');
          return;
        }
        if (d.data?.job_id) {
          setCurrentJobId(d.data.job_id);
        }
      })
      .catch(() => {
        setInitialLoading(false);
        setInitialError('Error de red');
      });
  }, [workspaceId]);

  const fetchJobs = useCallback((leadId: number) => {
    fetchWithAuth(`${API_URL}/v1/jobs?lead_id=${leadId}&active_only=false`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.jobs) {
          setJobs(d.data.jobs.map((j: Job) => ({ job_id: j.job_id, status: j.status, created_at: j.created_at })));
          setJobIndex(0);
        }
      })
      .catch(() => {});
  }, [workspaceId]);

  const navigate = useCallback((direction: 'prev' | 'next') => {
    const newIdx = direction === 'prev' ? jobIndex - 1 : jobIndex + 1;
    if (newIdx >= 0 && newIdx < jobs.length) {
      jobLog.cleanup();
      setJobIndex(newIdx);
      setCurrentJobId(jobs[newIdx].job_id);
    }
  }, [jobIndex, jobs, jobLog]);

  const handleCancel = useCallback(() => {
    if (!currentJobId) return;
    setCancelling(true);
    fetchWithAuth(`${API_URL}/v1/jobs/${currentJobId}/cancel`, { method: 'POST', headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (d.error) setInitialError(d.error.message || 'No se pudo cancelar');
        else jobLog.refetch();
      })
      .catch(() => setInitialError('Error de red'))
      .finally(() => setCancelling(false));
  }, [currentJobId, workspaceId, jobLog]);

  const reset = useCallback(() => {
    setCurrentJobId(null);
    setJobs([]);
    setJobIndex(0);
    setInitialError(null);
  }, []);

  const cleanup = useCallback(() => {
    jobLog.cleanup();
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }, [jobLog]);

  useEffect(() => {
    if (!lead) return;
    reset();
    fetchLeadLog(lead.id);
    fetchJobs(lead.id);
  }, [lead, fetchLeadLog, fetchJobs, reset]);

  return {
    lines: jobLog.lines,
    entries: jobLog.entries,
    status: jobLog.status,
    loading: initialLoading || jobLog.loading,
    error: initialError || jobLog.error,
    jobId: currentJobId,
    jobs,
    jobIndex,
    cancelling,
    navigate,
    handleCancel,
    cleanup,
  };
}
