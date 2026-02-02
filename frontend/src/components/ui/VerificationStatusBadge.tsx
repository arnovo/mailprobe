'use client';

import { useTranslations } from 'next-intl';

interface VerificationStatusBadgeProps {
  status: string;
  webMentioned?: boolean;
  smtpBlocked?: boolean;
  provider?: string;
  reason?: string;
}

const PROVIDER_LABELS: Record<string, string> = {
  google: 'Google Workspace',
  microsoft: 'Microsoft 365',
  ionos: 'IONOS',
  barracuda: 'Barracuda',
  proofpoint: 'Proofpoint',
  mimecast: 'Mimecast',
  ovh: 'OVH',
  zoho: 'Zoho',
  yahoo: 'Yahoo',
  icloud: 'iCloud',
};

export function VerificationStatusBadge({ 
  status, 
  webMentioned, 
  smtpBlocked,
  provider,
  reason,
}: VerificationStatusBadgeProps) {
  const t = useTranslations('verification');
  const providerLabel = provider && provider !== 'other' ? PROVIDER_LABELS[provider] || provider : null;

  return (
    <span>
      {status === 'pending' && (
        <span style={{ color: '#94a3b8' }}>{t('status.pending')}</span>
      )}
      {status === 'valid' && (
        <span style={{ color: '#4ade80', fontWeight: 500 }}>✓ {t('status.valid')}</span>
      )}
      {status === 'risky' && (
        <span 
          style={{ color: '#fbbf24' }} 
          title={reason || (smtpBlocked 
            ? t('noSmtpNote')
            : 'Server accepts emails but has catch-all active')}
        >
          ⚠ {t('status.risky')}
        </span>
      )}
      {status === 'unknown' && (
        <>
          <span 
            style={{ color: '#f97316' }} 
            title={reason || 'Could not verify via SMTP (firewall, timeout). Email shown is the most likely candidate.'}
          >
            ? {t('status.unknown')}
          </span>
          <span style={{ display: 'block', fontSize: '0.7rem', color: '#a1a1aa', marginTop: '0.125rem' }}>
            Server not responding
          </span>
        </>
      )}
      {status === 'invalid' && (
        <span style={{ color: '#ef4444' }}>✗ {t('status.invalid')}</span>
      )}
      
      {/* SMTP blocked indicator */}
      {smtpBlocked && status !== 'invalid' && status !== 'pending' && (
        <span 
          style={{ display: 'block', fontSize: '0.65rem', color: '#a78bfa', marginTop: '0.125rem' }}
          title={t('smtpBlockedMessage')}
        >
          ⚡ {t('signals.smtpBlocked')}
        </span>
      )}
      
      {/* Provider indicator */}
      {providerLabel && status !== 'invalid' && status !== 'pending' && (
        <span 
          style={{ display: 'block', fontSize: '0.65rem', color: '#60a5fa', marginTop: '0.125rem' }}
          title={t('signals.provider', { provider: providerLabel })}
        >
          📧 {providerLabel}
        </span>
      )}
      
      {/* Web mentioned indicator */}
      {webMentioned && (
        <span 
          style={{ display: 'block', fontSize: '0.7rem', color: '#4ade80', marginTop: '0.125rem' }} 
          title="Email found on public pages (web search), increasing reliability."
        >
          ✓ {t('signals.web')}
        </span>
      )}
    </span>
  );
}
