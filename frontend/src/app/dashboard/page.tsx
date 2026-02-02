'use client';

/**
 * Página principal del dashboard: listado de leads del workspace.
 * Refactorizado para usar componentes modulares y hooks personalizados.
 */

import { useState } from 'react';
import { useAuth, useLeads, useVerification, Lead } from '@/hooks';
import { TerminalLog } from '@/components/ui';
import { LeadsTable, LogModal, AlertsModal } from '@/components/leads';

interface AlertsData {
  leadId: number;
  leadName: string;
  alerts: string[];
  firstName: string;
  lastName: string;
}

export default function DashboardPage() {
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
    return <div className="card"><p>Cargando...</p></div>;
  }

  return (
    <div className="card">
      <h2>Leads</h2>
      <p style={{ marginBottom: '1rem', color: '#94a3b8', fontSize: '0.875rem' }}>
        Para buscar el email de un contacto: usa el botón &quot;Verificar&quot;. Se encola un job (worker de Celery);
        si el worker no está en marcha, el job no se ejecuta. Comprueba con <code>docker compose ps</code> que
        <code>mailprobe-worker-1</code> esté Up.
      </p>

      {message && (
        <p style={{ marginBottom: '1rem', padding: '0.5rem', background: '#0f172a', borderRadius: '0.375rem', fontSize: '0.875rem' }}>
          {message}
        </p>
      )}

      {logLines.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <TerminalLog lines={logLines} aria-label="Log de verificación" />
        </div>
      )}

      {loading ? (
        <p>Cargando...</p>
      ) : (
        <>
          <LeadsTable
            leads={leads}
            verifyingId={verifyingId}
            onViewLog={handleViewLog}
            onVerify={verify}
            onAlertClick={handleAlertClick}
          />
          {leads.length === 0 && <p>No hay leads. Crea uno por API o importa CSV.</p>}
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
