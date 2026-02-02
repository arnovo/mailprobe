'use client';

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
  const providerLabel = provider && provider !== 'other' ? PROVIDER_LABELS[provider] || provider : null;

  return (
    <span>
      {status === 'pending' && (
        <span style={{ color: '#94a3b8' }}>Sin verificar</span>
      )}
      {status === 'valid' && (
        <span style={{ color: '#4ade80', fontWeight: 500 }}>✓ Verificado</span>
      )}
      {status === 'risky' && (
        <span 
          style={{ color: '#fbbf24' }} 
          title={reason || (smtpBlocked 
            ? 'SMTP no disponible en este entorno. Resultado basado en DNS y patrones.' 
            : 'El servidor acepta emails pero tiene catch-all activo')}
        >
          ⚠ Probable
        </span>
      )}
      {status === 'unknown' && (
        <>
          <span 
            style={{ color: '#f97316' }} 
            title={reason || 'No se pudo verificar por SMTP (firewall, timeout). El email mostrado es el candidato más probable.'}
          >
            ? No verificable
          </span>
          <span style={{ display: 'block', fontSize: '0.7rem', color: '#a1a1aa', marginTop: '0.125rem' }}>
            Servidor no responde
          </span>
        </>
      )}
      {status === 'invalid' && (
        <span style={{ color: '#ef4444' }}>✗ Inválido</span>
      )}
      
      {/* SMTP blocked indicator */}
      {smtpBlocked && status !== 'invalid' && status !== 'pending' && (
        <span 
          style={{ display: 'block', fontSize: '0.65rem', color: '#a78bfa', marginTop: '0.125rem' }}
          title="El puerto SMTP (25) está bloqueado en este entorno. El resultado se basa en señales DNS y patrones."
        >
          ⚡ Sin SMTP
        </span>
      )}
      
      {/* Provider indicator */}
      {providerLabel && status !== 'invalid' && status !== 'pending' && (
        <span 
          style={{ display: 'block', fontSize: '0.65rem', color: '#60a5fa', marginTop: '0.125rem' }}
          title={`Proveedor de email detectado: ${providerLabel}`}
        >
          📧 {providerLabel}
        </span>
      )}
      
      {/* Web mentioned indicator */}
      {webMentioned && (
        <span 
          style={{ display: 'block', fontSize: '0.7rem', color: '#4ade80', marginTop: '0.125rem' }} 
          title="El email aparece en páginas públicas (búsqueda web), lo que aumenta su fiabilidad."
        >
          ✓ Encontrado en web
        </span>
      )}
    </span>
  );
}
