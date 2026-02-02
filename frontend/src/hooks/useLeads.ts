'use client';

import { useCallback, useEffect, useState } from 'react';
import { fetchWithAuth } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Lead {
  id: number;
  first_name: string;
  last_name: string;
  company: string;
  domain: string;
  email_best: string;
  verification_status: string;
  confidence_score: number;
  // DNS signals
  mx_found: boolean;
  spf_present: boolean;
  dmarc_present: boolean;
  // SMTP signals
  catch_all: boolean | null;
  smtp_check: boolean;
  smtp_attempted: boolean;
  smtp_blocked: boolean;
  // Additional signals
  provider: string;
  web_mentioned: boolean;
  signals: string[];
  notes: string;
  // Job status
  last_job_status: string | null;
  linkedin_url?: string;
  job_title?: string;
}

interface UseLeadsOptions {
  token: string | null;
  workspaceId: string;
  page?: number;
  pageSize?: number;
}

export function useLeads({ token, workspaceId, page = 1, pageSize = 20 }: UseLeadsOptions) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLeads = useCallback(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    
    fetchWithAuth(`${API_URL}/v1/leads?page=${page}&page_size=${pageSize}`, {
      headers: { 'X-Workspace-Id': workspaceId },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.items) {
          setLeads(d.data.items);
        }
        if (d.error) {
          setError(d.error.message || 'errors.loadLeads');
        }
      })
      .catch(() => setError('errors.networkError'))
      .finally(() => setLoading(false));
  }, [token, workspaceId, page, pageSize]);

  useEffect(() => {
    if (token) {
      loadLeads();
    }
  }, [token, loadLeads]);

  return { leads, loading, error, reload: loadLeads };
}
