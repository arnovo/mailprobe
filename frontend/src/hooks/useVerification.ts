'use client';

import { fetchWithAuth } from '@/lib/auth';
import { useCallback, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Timing constants (milliseconds)
const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 30000;
const MESSAGE_DISPLAY_SUCCESS_MS = 4000;
const MESSAGE_DISPLAY_ERROR_MS = 6000;
const MESSAGE_DISPLAY_SHORT_MS = 3000;
const MESSAGE_DISPLAY_VERIFY_ERROR_MS = 5000;

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
            setTimeout(() => { setMessage(null); setLogLines([]); }, MESSAGE_DISPLAY_SUCCESS_MS);
          } else if (status === 'failed') {
            clearInterval(interval);
            setMessage(`Error: ${d.data?.error || 'Job fallido'}`);
            setVerifyingId(null);
            setTimeout(() => { setMessage(null); setLogLines([]); }, MESSAGE_DISPLAY_ERROR_MS);
          }
        })
        .catch(() => {
          clearInterval(interval);
          setVerifyingId(null);
          setMessage(null);
          setLogLines([]);
        });
    }, POLL_INTERVAL_MS);

    // Timeout after poll timeout
    setTimeout(() => {
      clearInterval(interval);
      setVerifyingId(null);
      setMessage(null);
      setLogLines([]);
    }, POLL_TIMEOUT_MS);
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
          setTimeout(() => setMessage(null), MESSAGE_DISPLAY_VERIFY_ERROR_MS);
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
        setTimeout(() => setMessage(null), MESSAGE_DISPLAY_SHORT_MS);
        setVerifyingId(null);
      });
  }, [workspaceId, pollJobUntilDone]);

  return { verify, verifyingId, message, logLines };
}
