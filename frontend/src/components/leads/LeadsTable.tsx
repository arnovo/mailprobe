'use client';

import { useTranslations } from 'next-intl';
import { JobStatusBadge, SignalsBadges, VerificationStatusBadge } from '@/components/ui';
import { Lead } from '@/hooks/useLeads';

interface LeadsTableProps {
  leads: Lead[];
  verifyingId: number | null;
  onViewLog: (lead: Lead) => void;
  onVerify: (leadId: number) => void;
  onAlertClick: (lead: Lead, alerts: string[]) => void;
}

export function LeadsTable({ leads, verifyingId, onViewLog, onVerify, onAlertClick }: LeadsTableProps) {
  const t = useTranslations('leads');

  const getAlerts = (lead: Lead): string[] => {
    const alerts: string[] = [];
    if (!lead.last_name) alerts.push('Missing last name. Add last name or enable "Allow leads without last name" in Settings.');
    if (!lead.domain) alerts.push('Missing domain. Add a domain to verify.');
    return alerts;
  };

  return (
    <table className="leads-table">
      <thead>
        <tr>
          <th style={{ width: '25%' }}>{t('firstName')}</th>
          <th style={{ width: '30%' }}>{t('emailBest')}</th>
          <th style={{ width: '25%' }}>{t('verificationStatus')}</th>
          <th style={{ width: '20%', textAlign: 'right' }}>{t('actions') || 'Actions'}</th>
        </tr>
      </thead>
      <tbody>
        {leads.map((lead) => {
          const alerts = getAlerts(lead);
          const fullName = [lead.first_name, lead.last_name].filter(Boolean).join(' ');
          
          return (
            <tr key={lead.id}>
              {/* Contact: Name + Company */}
              <td>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontWeight: 500 }}>
                    {fullName || '—'}
                    {alerts.length > 0 && (
                      <button
                        type="button"
                        onClick={() => onAlertClick(lead, alerts)}
                        style={{ 
                          background: 'none', 
                          border: 'none', 
                          cursor: 'pointer', 
                          padding: 0, 
                          fontSize: '0.875rem', 
                          lineHeight: 1,
                          opacity: 0.9
                        }}
                        title={t('alerts')}
                      >
                        ⚠️
                      </button>
                    )}
                  </span>
                  {lead.company && (
                    <span style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>
                      {lead.company}
                    </span>
                  )}
                </div>
              </td>

              {/* Email */}
              <td>
                <span style={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.875rem',
                  color: lead.email_best ? '#e2e8f0' : '#64748b'
                }}>
                  {lead.email_best || '—'}
                </span>
              </td>

              {/* Verification: Status + Signals + Job badge */}
              <td>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <VerificationStatusBadge 
                    status={lead.verification_status} 
                    webMentioned={lead.web_mentioned}
                    smtpBlocked={lead.smtp_blocked}
                    provider={lead.provider}
                    reason={lead.notes}
                  />
                  {/* Show DNS signals if verified */}
                  {lead.verification_status !== 'pending' && lead.signals && lead.signals.length > 0 && (
                    <SignalsBadges signals={lead.signals} compact />
                  )}
                  {/* Only show job status if useful: error, queued or running */}
                  {lead.last_job_status && ['failed', 'cancelled', 'running', 'queued'].includes(lead.last_job_status) && (
                    <div style={{ marginTop: '0.125rem' }}>
                      <JobStatusBadge status={lead.last_job_status} />
                    </div>
                  )}
                </div>
              </td>

              {/* Actions */}
              <td>
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                  <button 
                    type="button" 
                    onClick={() => onViewLog(lead)} 
                    title={t('viewLog')}
                    className="btn-secondary btn-sm"
                  >
                    Log
                  </button>
                  {lead.domain && (
                    <button
                      type="button"
                      onClick={() => onVerify(lead.id)}
                      disabled={verifyingId === lead.id}
                      className="btn-primary btn-sm"
                    >
                      {verifyingId === lead.id ? '...' : t('verify')}
                    </button>
                  )}
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
