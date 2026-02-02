'use client';

import { SerperUsage } from '@/hooks/useConfig';

interface WebSearchSettingsProps {
  provider: string;
  apiKey: string;
  serperUsage: SerperUsage | null;
  onProviderChange: (v: string) => void;
  onApiKeyChange: (v: string) => void;
  onLoadSerperUsage: () => void;
}

export function WebSearchSettings({
  provider,
  apiKey,
  serperUsage,
  onProviderChange,
  onApiKeyChange,
  onLoadSerperUsage,
}: WebSearchSettingsProps) {
  const handleProviderChange = (newProvider: string) => {
    onProviderChange(newProvider);
    if (newProvider === 'serper') {
      onLoadSerperUsage();
    }
  };

  return (
    <div style={{ borderTop: '1px solid #334155', paddingTop: '1rem', marginTop: '0.5rem' }}>
      <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', color: '#e2e8f0' }}>
        Búsqueda web (opcional)
      </h3>
      <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
        Si SMTP no responde (firewall, Barracuda...), se busca si el email aparece en páginas públicas.
      </p>
      
      <label htmlFor="config-websearch-provider" style={{ display: 'block', marginBottom: '0.25rem', color: '#e2e8f0' }}>
        Provider
      </label>
      <select
        id="config-websearch-provider"
        value={provider}
        onChange={(e) => handleProviderChange(e.target.value)}
        style={{ padding: '0.5rem', width: '100%', maxWidth: 200, background: '#0f172a', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0' }}
      >
        <option value="">— No usar —</option>
        <option value="serper">Serper.dev (Google)</option>
        <option value="bing">Bing (deprecado)</option>
      </select>

      {provider && (
        <div style={{ marginTop: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.25rem' }}>
            <label style={{ color: '#e2e8f0' }}>
              API Key ({provider === 'serper' ? 'Serper.dev' : 'Bing'})
            </label>
            {provider === 'serper' && serperUsage && (
              <span
                style={{
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.5rem',
                  borderRadius: 4,
                  background: serperUsage.current_month >= 2400 ? '#7f1d1d' : serperUsage.current_month >= 2000 ? '#78350f' : '#1e3a5f',
                  color: serperUsage.current_month >= 2400 ? '#fca5a5' : serperUsage.current_month >= 2000 ? '#fcd34d' : '#93c5fd',
                }}
              >
                Uso: {serperUsage.current_month.toLocaleString()} / 2,500 ({serperUsage.month_key})
              </span>
            )}
          </div>
          <input
            type="text"
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            placeholder="Tu API key aquí"
            style={{ padding: '0.5rem', width: '100%', maxWidth: 320, background: '#0f172a', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0' }}
          />
          <p style={{ marginTop: '0.25rem', color: '#94a3b8', fontSize: '0.75rem' }}>
            {provider === 'serper' && 'Serper.dev: 2500 búsquedas/mes gratis. https://serper.dev'}
            {provider === 'bing' && 'Bing Web Search API (retirada agosto 2025).'}
            {apiKey.startsWith('*') && ' — La clave actual está oculta; déjala igual para no cambiarla.'}
          </p>
        </div>
      )}
    </div>
  );
}
