'use client';

/**
 * Dashboard main page: leads list for the workspace.
 * Refactored to use modular components and custom hooks.
 */

import { AlertsModal, LeadsTable, LogModal } from '@/components/leads';
import { TerminalLog } from '@/components/ui';
import { Lead, useAuth, useLeads, useVerification } from '@/hooks';
import { useTranslations } from 'next-intl';
import { useState } from 'react';

interface AlertsData {
  leadId: number;
  leadName: string;
  alerts: string[];
  firstName: string;
  lastName: string;
}

export function LeadsPage() {
  const t = useTranslations('leads');
  const tCommon = useTranslations('common');
  const { token, workspaceId } = useAuth();
  const { leads, loading, reload } = useLeads({ token, workspaceId });
  const { verify, verifyingId, message, logLines } = useVerification({ 
    workspaceId, 
    onComplete: reload 
  });

  const [logModalLead, setLogModalLead] = useState<{ id: number; name: string } | null>(null);
  const [alertsModal, setAlertsModal] = useState<AlertsData | null>(null);

  const handleViewLog = (lead: Lead) => {
    const name = [lead.first_name, lead.last_name].filter(Boolean).join(' ') || `Lead #${lead.id}`;
    setLogModalLead({ id: lead.id, name });
  };

  const handleAlertClick = (lead: Lead, alerts: string[]) => {
    setAlertsModal({
      leadId: lead.id,
      leadName: `${lead.first_name} ${lead.last_name}`.trim() || `Lead #${lead.id}`,
      alerts,
      firstName: lead.first_name || '',
      lastName: lead.last_name || '',
    });
  };

  if (!token) {
    return <div className="card"><p>{tCommon('loading')}</p></div>;
  }

  return (
    <div className="card">
      <h2>{t('title')}</h2>

      {message && (
        <p style={{ marginBottom: '1rem', padding: '0.5rem', background: '#0f172a', borderRadius: '0.375rem', fontSize: '0.875rem' }}>
          {message}
        </p>
      )}

      {logLines.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <TerminalLog lines={logLines} aria-label="Verification log" />
        </div>
      )}

      {loading ? (
        <p>{tCommon('loading')}</p>
      ) : (
        <>
          <LeadsTable
            leads={leads}
            verifyingId={verifyingId}
            onViewLog={handleViewLog}
            onVerify={verify}
            onAlertClick={handleAlertClick}
          />
          {leads.length === 0 && <p>{t('noLeads')}</p>}
        </>
      )}

      <LogModal
        lead={logModalLead}
        workspaceId={workspaceId}
        onClose={() => setLogModalLead(null)}
      />

      <AlertsModal
        data={alertsModal}
        workspaceId={workspaceId}
        onClose={() => setAlertsModal(null)}
        onSaved={reload}
      />
    </div>
  );
}
