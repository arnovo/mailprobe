'use client';

/**
 * Configuración del workspace: timeouts SMTP/DNS y patrones de candidatos de email.
 * Refactorizado para usar componentes modulares y hooks personalizados.
 */

import { useAuth, useConfig, CONFIG_CONSTANTS } from '@/hooks';
import { TimeoutSettings, WebSearchSettings, PatternSettings } from '@/components/config';

const { MIN_TIMEOUT, MAX_TIMEOUT, MIN_PATTERNS } = CONFIG_CONSTANTS;

export default function ConfigPage() {
  const { token, workspaceId } = useAuth();
  const { 
    config, 
    updateConfig, 
    loading, 
    saving, 
    error, 
    success, 
    save, 
    serperUsage, 
    loadSerperUsage 
  } = useConfig({ token, workspaceId });

  const togglePattern = (i: number) => {
    const next = config.enabledIndices.includes(i)
      ? config.enabledIndices.filter((x) => x !== i)
      : [...config.enabledIndices, i].sort((a, b) => a - b);
    updateConfig({ enabledIndices: next });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (config.enabledIndices.length < MIN_PATTERNS) return;
    save(config);
  };

  if (!token) {
    return <div className="card"><p>Cargando...</p></div>;
  }

  return (
    <div className="card">
      <h2>Configuración del workspace</h2>
      <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>
        Timeouts y patrones de candidatos de email para la verificación. Si no defines valores, se usan los globales.
        Timeouts: {MIN_TIMEOUT}–{MAX_TIMEOUT} s. Mínimo {MIN_PATTERNS} patrones habilitados.
      </p>

      {error && <p style={{ color: '#f87171', marginBottom: '0.5rem' }}>{error}</p>}
      {success && <p style={{ color: '#4ade80', marginBottom: '0.5rem' }}>{success}</p>}

      {loading ? (
        <p>Cargando...</p>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: 520 }}>
          <TimeoutSettings
            smtpTimeout={config.smtpTimeout}
            dnsTimeout={config.dnsTimeout}
            smtpMailFrom={config.smtpMailFrom}
            onSmtpTimeoutChange={(v) => updateConfig({ smtpTimeout: v })}
            onDnsTimeoutChange={(v) => updateConfig({ dnsTimeout: v })}
            onMailFromChange={(v) => updateConfig({ smtpMailFrom: v })}
          />

          <WebSearchSettings
            provider={config.webSearchProvider}
            apiKey={config.webSearchApiKey}
            serperUsage={serperUsage}
            onProviderChange={(v) => updateConfig({ webSearchProvider: v })}
            onApiKeyChange={(v) => updateConfig({ webSearchApiKey: v })}
            onLoadSerperUsage={loadSerperUsage}
          />

          <PatternSettings
            enabledIndices={config.enabledIndices}
            patternLabels={config.patternLabels}
            allowNoLastname={config.allowNoLastname}
            customPatterns={config.customPatterns}
            onTogglePattern={togglePattern}
            onAllowNoLastnameChange={(v) => updateConfig({ allowNoLastname: v })}
            onCustomPatternsChange={(patterns) => updateConfig({ customPatterns: patterns })}
          />

          <button
            type="submit"
            disabled={saving || config.enabledIndices.length < MIN_PATTERNS}
            style={{ 
              padding: '0.5rem 1rem', 
              alignSelf: 'flex-start', 
              cursor: saving || config.enabledIndices.length < MIN_PATTERNS ? 'not-allowed' : 'pointer' 
            }}
          >
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </form>
      )}
    </div>
  );
}
