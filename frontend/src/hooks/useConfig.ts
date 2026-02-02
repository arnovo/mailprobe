'use client';

import { fetchWithAuth } from '@/lib/auth';
import { useCallback, useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ConfigData {
  smtpTimeout: number;
  dnsTimeout: number;
  smtpMailFrom: string;
  webSearchProvider: string;
  webSearchApiKey: string;
  allowNoLastname: boolean;
  enabledIndices: number[];
  patternLabels: string[];
  customPatterns: string[];
}

export interface SerperUsage {
  current_month: number;
  total: number;
  month_key: string;
}

const MIN_TIMEOUT = 1;
const MAX_TIMEOUT = 30;

interface UseConfigOptions {
  token: string | null;
  workspaceId: string;
}

export function useConfig({ token, workspaceId }: UseConfigOptions) {
  const [config, setConfig] = useState<ConfigData>({
    smtpTimeout: 5,
    dnsTimeout: 5,
    smtpMailFrom: 'noreply@mailcheck.local',
    webSearchProvider: '',
    webSearchApiKey: '',
    allowNoLastname: false,
    enabledIndices: [],
    patternLabels: [],
    customPatterns: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [serperUsage, setSerperUsage] = useState<SerperUsage | null>(null);

  const loadSerperUsage = useCallback(() => {
    if (!token) return;
    fetchWithAuth(`${API_URL}/v1/config/serper-usage`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => { if (d.data) setSerperUsage(d.data); })
      .catch(() => {});
  }, [token, workspaceId]);

  const load = useCallback(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    fetchWithAuth(`${API_URL}/v1/config`, { headers: { 'X-Workspace-Id': workspaceId } })
      .then((r) => r.json())
      .then((d) => {
        if (d.error) {
          setError(d.error.message || 'Error al cargar configuración');
          return;
        }
        const c = d.data;
        const provider = typeof c.web_search_provider === 'string' ? c.web_search_provider : '';
        setConfig({
          smtpTimeout: Math.max(MIN_TIMEOUT, Math.min(MAX_TIMEOUT, c.smtp_timeout_seconds)),
          dnsTimeout: Math.max(MIN_TIMEOUT, Math.min(MAX_TIMEOUT, c.dns_timeout_seconds)),
          smtpMailFrom: c.smtp_mail_from || 'noreply@mailcheck.local',
          webSearchProvider: provider,
          webSearchApiKey: c.web_search_api_key || '',
          allowNoLastname: c.allow_no_lastname === true,
          enabledIndices: Array.isArray(c.enabled_pattern_indices) ? c.enabled_pattern_indices : [],
          patternLabels: Array.isArray(c.pattern_labels) ? c.pattern_labels : [],
          customPatterns: Array.isArray(c.custom_patterns) ? c.custom_patterns : [],
        });
        if (provider === 'serper') loadSerperUsage();
      })
      .catch(() => setError('Error de red'))
      .finally(() => setLoading(false));
  }, [token, workspaceId, loadSerperUsage]);

  useEffect(() => {
    if (token) load();
  }, [token, load]);

  const save = useCallback(async (data: Partial<ConfigData>) => {
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      const res = await fetchWithAuth(`${API_URL}/v1/config`, {
        method: 'PUT',
        headers: { 'X-Workspace-Id': workspaceId, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          smtp_timeout_seconds: data.smtpTimeout,
          dns_timeout_seconds: data.dnsTimeout,
          smtp_mail_from: data.smtpMailFrom?.trim() || null,
          web_search_provider: data.webSearchProvider?.trim() || null,
          web_search_api_key: data.webSearchApiKey?.startsWith('*') ? undefined : (data.webSearchApiKey?.trim() || null),
          allow_no_lastname: data.allowNoLastname,
          enabled_pattern_indices: data.enabledIndices,
          custom_patterns: data.customPatterns,
        }),
      });
      const d = await res.json();
      if (d.error) {
        setError(d.error.message || 'Error al guardar');
      } else {
        setSuccess('Configuración guardada.');
        setTimeout(() => setSuccess(null), 4000);
      }
    } catch {
      setError('Error de red');
    } finally {
      setSaving(false);
    }
  }, [workspaceId]);

  const updateConfig = (updates: Partial<ConfigData>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  };

  return { 
    config, 
    updateConfig, 
    loading, 
    saving, 
    error, 
    success, 
    save, 
    serperUsage, 
    loadSerperUsage 
  };
}

export const CONFIG_CONSTANTS = { MIN_TIMEOUT, MAX_TIMEOUT, MIN_PATTERNS: 5 };
