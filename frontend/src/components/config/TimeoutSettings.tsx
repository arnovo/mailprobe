'use client';

import { CONFIG_CONSTANTS } from '@/hooks/useConfig';

const { MIN_TIMEOUT, MAX_TIMEOUT } = CONFIG_CONSTANTS;

interface TimeoutSettingsProps {
  smtpTimeout: number;
  dnsTimeout: number;
  smtpMailFrom: string;
  onSmtpTimeoutChange: (v: number) => void;
  onDnsTimeoutChange: (v: number) => void;
  onMailFromChange: (v: string) => void;
}

export function TimeoutSettings({
  smtpTimeout,
  dnsTimeout,
  smtpMailFrom,
  onSmtpTimeoutChange,
  onDnsTimeoutChange,
  onMailFromChange,
}: TimeoutSettingsProps) {
  return (
    <>
      <div>
        <label htmlFor="config-smtp-timeout" style={{ display: 'block', marginBottom: '0.25rem', color: '#e2e8f0' }}>
          Timeout SMTP (segundos)
        </label>
        <input
          id="config-smtp-timeout"
          type="number"
          min={MIN_TIMEOUT}
          max={MAX_TIMEOUT}
          value={smtpTimeout}
          onChange={(e) => onSmtpTimeoutChange(Number(e.target.value) || MIN_TIMEOUT)}
          style={{ padding: '0.5rem', width: 80, background: '#0f172a', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0' }}
        />
        <span style={{ marginLeft: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
          {MIN_TIMEOUT}–{MAX_TIMEOUT} s
        </span>
      </div>

      <div>
        <label htmlFor="config-mail-from" style={{ display: 'block', marginBottom: '0.25rem', color: '#e2e8f0' }}>
          MAIL FROM (dirección usada en la sonda SMTP)
        </label>
        <input
          id="config-mail-from"
          type="text"
          value={smtpMailFrom}
          onChange={(e) => onMailFromChange(e.target.value)}
          placeholder="noreply@mailcheck.local"
          style={{ padding: '0.5rem', width: '100%', maxWidth: 320, background: '#0f172a', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0' }}
        />
        <p style={{ marginTop: '0.25rem', color: '#94a3b8', fontSize: '0.875rem' }}>
          Vacío = usar valor global del servidor. Recomendado: noreply@tudominio.com
        </p>
      </div>

      <div>
        <label htmlFor="config-dns-timeout" style={{ display: 'block', marginBottom: '0.25rem', color: '#e2e8f0' }}>
          Timeout DNS (segundos)
        </label>
        <input
          id="config-dns-timeout"
          type="number"
          min={MIN_TIMEOUT}
          max={MAX_TIMEOUT}
          step={0.5}
          value={dnsTimeout}
          onChange={(e) => onDnsTimeoutChange(Number(e.target.value) || MIN_TIMEOUT)}
          style={{ padding: '0.5rem', width: 80, background: '#0f172a', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0' }}
        />
        <span style={{ marginLeft: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
          {MIN_TIMEOUT}–{MAX_TIMEOUT} s
        </span>
      </div>
    </>
  );
}
