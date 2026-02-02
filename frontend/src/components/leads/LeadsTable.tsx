'use client';

import { Lead } from '@/hooks/useLeads';
import { VerificationStatusBadge, JobStatusBadge } from '@/components/ui';

interface LeadsTableProps {
  leads: Lead[];
  verifyingId: number | null;
  onViewLog: (lead: Lead) => void;
  onVerify: (leadId: number) => void;
  onAlertClick: (lead: Lead, alerts: string[]) => void;
}

export function LeadsTable({ leads, verifyingId, onViewLog, onVerify, onAlertClick }: LeadsTableProps) {
  const getAlerts = (lead: Lead): string[] => {
    const alerts: string[] = [];
    if (!lead.last_name) alerts.push('Sin apellido. Añade apellido o activa "Permitir leads sin apellido" en Configuración.');
    if (!lead.domain) alerts.push('Sin dominio. Añade un dominio para poder verificar.');
    return alerts;
  };

  return (
    <table className="leads-table">
      <thead>
        <tr>
          <th style={{ width: '25%' }}>Contacto</th>
          <th style={{ width: '30%' }}>Email</th>
          <th style={{ width: '25%' }}>Verificación</th>
          <th style={{ width: '20%', textAlign: 'right' }}>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {leads.map((lead) => {
          const alerts = getAlerts(lead);
          const fullName = [lead.first_name, lead.last_name].filter(Boolean).join(' ');
          
          return (
            <tr key={lead.id}>
              {/* Contacto: Nombre + Empresa */}
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
                        title="Ver alertas"
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
                  {lead.email_best || 'Sin email'}
                </span>
              </td>

              {/* Verificación: Estado + Job badge solo si hay problema */}
              <td>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <VerificationStatusBadge 
                    status={lead.verification_status} 
                    webMentioned={lead.web_mentioned} 
                  />
                  {/* Solo mostrar job status si es útil: error, en cola o ejecutando */}
                  {lead.last_job_status && ['failed', 'cancelled', 'running', 'queued'].includes(lead.last_job_status) && (
                    <div style={{ marginTop: '0.125rem' }}>
                      <JobStatusBadge status={lead.last_job_status} />
                    </div>
                  )}
                </div>
              </td>

              {/* Acciones */}
              <td>
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                  <button 
                    type="button" 
                    onClick={() => onViewLog(lead)} 
                    title="Ver log de verificación"
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
                      {verifyingId === lead.id ? '...' : 'Verificar'}
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
