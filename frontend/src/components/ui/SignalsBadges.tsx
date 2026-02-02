'use client';

interface SignalsBadgesProps {
  signals: string[];
  compact?: boolean;
}

const SIGNAL_CONFIG: Record<string, { label: string; color: string; title: string }> = {
  mx: { 
    label: 'MX', 
    color: '#4ade80', 
    title: 'Registros MX encontrados' 
  },
  spf: { 
    label: 'SPF', 
    color: '#60a5fa', 
    title: 'SPF configurado (protección anti-spoofing)' 
  },
  dmarc: { 
    label: 'DMARC', 
    color: '#818cf8', 
    title: 'DMARC configurado (política de autenticación)' 
  },
  web: { 
    label: 'Web', 
    color: '#34d399', 
    title: 'Email encontrado en fuentes públicas' 
  },
  smtp_blocked: { 
    label: 'SMTP⚡', 
    color: '#f97316', 
    title: 'Puerto SMTP bloqueado en este entorno' 
  },
};

export function SignalsBadges({ signals, compact = false }: SignalsBadgesProps) {
  if (!signals || signals.length === 0) {
    return null;
  }

  // Filter to known signals and extract provider if present
  const knownSignals = signals.filter(s => SIGNAL_CONFIG[s]);
  const providerSignal = signals.find(s => s.startsWith('provider:'));
  
  if (knownSignals.length === 0 && !providerSignal) {
    return null;
  }

  const badgeStyle = {
    display: 'inline-block',
    padding: compact ? '0.1rem 0.25rem' : '0.15rem 0.35rem',
    fontSize: compact ? '0.6rem' : '0.65rem',
    fontWeight: 500,
    borderRadius: '0.25rem',
    marginRight: '0.25rem',
    marginBottom: '0.125rem',
  };

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.125rem' }}>
      {knownSignals.map((signal) => {
        const config = SIGNAL_CONFIG[signal];
        return (
          <span
            key={signal}
            style={{
              ...badgeStyle,
              backgroundColor: `${config.color}20`,
              color: config.color,
              border: `1px solid ${config.color}40`,
            }}
            title={config.title}
          >
            {config.label}
          </span>
        );
      })}
    </div>
  );
}
