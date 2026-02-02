'use client';

import { useCallback, useState } from 'react';
import { fetchWithAuth } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseVerificationOptions {
  workspaceId: string;
  onComplete?: () => void;
}

export function useVerification({ workspaceId, onComplete }: UseVerificationOptions) {
  const [verifyingId, setVerifyingId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [logLines, setLogLines] = useState<string[]>([]);

  const pollJobUntilDone = useCallback((jobId: string) => {
    const interval = setInterval(() => {
      fetchWithAuth(`${API_URL}/v1/jobs/${jobId}`, { headers: { 'X-Workspace-Id': workspaceId } })
        .then((r) => r.json())
        .then((d) => {
          if (d.error) {
            clearInterval(interval);
            setVerifyingId(null);
            setMessage(null);
            setLogLines([]);
            return;
          }
          const lines = d.data?.log_lines;
          if (Array.isArray(lines) && lines.length > 0) setLogLines(lines);
          const status = d.data?.status;
          if (status === 'succeeded') {
            clearInterval(interval);
            setMessage('Listo. Email actualizado.');
            onComplete?.();
            setVerifyingId(null);
            setTimeout(() => { setMessage(null); setLogLines([]); }, 4000);
          } else if (status === 'failed') {
            clearInterval(interval);
            setMessage(`Error: ${d.data?.error || 'Job fallido'}`);
            setVerifyingId(null);
            setTimeout(() => { setMessage(null); setLogLines([]); }, 6000);
          }
        })
        .catch(() => {
          clearInterval(interval);
          setVerifyingId(null);
          setMessage(null);
          setLogLines([]);
        });
    }, 2000);

    // Timeout after 30 seconds
    setTimeout(() => {
      clearInterval(interval);
      setVerifyingId(null);
      setMessage(null);
      setLogLines([]);
    }, 30000);
  }, [workspaceId, onComplete]);

  const verify = useCallback((leadId: number) => {
    setVerifyingId(leadId);
    setMessage('Encolando...');
    
    fetchWithAuth(`${API_URL}/v1/leads/${leadId}/verify`, {
      method: 'POST',
      headers: { 'X-Workspace-Id': workspaceId },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.error) {
          setMessage(`Error: ${d.error.message || d.error.code || 'Error'}`);
          setTimeout(() => setMessage(null), 5000);
          setVerifyingId(null);
          return;
        }
        if (d.data?.job_id) {
          setLogLines([]);
          setMessage('Verificando... (esperando worker).');
          pollJobUntilDone(d.data.job_id);
        }
      })
      .catch(() => {
        setMessage('Error de red');
        setTimeout(() => setMessage(null), 3000);
        setVerifyingId(null);
      });
  }, [workspaceId, pollJobUntilDone]);

  return { verify, verifyingId, message, logLines };
}
