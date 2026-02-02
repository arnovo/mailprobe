'use client';

interface VerificationStatusBadgeProps {
  status: string;
  webMentioned?: boolean;
}

export function VerificationStatusBadge({ status, webMentioned }: VerificationStatusBadgeProps) {
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
          title="El servidor acepta emails pero tiene catch-all activo"
        >
          ⚠ Probable
        </span>
      )}
      {status === 'unknown' && (
        <>
          <span 
            style={{ color: '#f97316' }} 
            title="No se pudo verificar por SMTP (firewall, timeout). El email mostrado es el candidato más probable."
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
