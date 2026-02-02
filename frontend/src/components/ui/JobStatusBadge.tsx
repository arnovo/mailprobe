'use client';

interface JobStatusBadgeProps {
  status: string | null;
}

const STATUS_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  succeeded: { bg: '#14532d', color: '#4ade80', label: 'Exitoso' },
  failed: { bg: '#7f1d1d', color: '#fca5a5', label: 'Fallido' },
  cancelled: { bg: '#78350f', color: '#fcd34d', label: 'Cancelado' },
  running: { bg: '#1e3a5f', color: '#93c5fd', label: 'Ejecutando' },
  queued: { bg: '#3f3f46', color: '#a1a1aa', label: 'En cola' },
};

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  if (!status) {
    return <span style={{ color: '#64748b', fontSize: '0.75rem' }}>—</span>;
  }

  const style = STATUS_STYLES[status] || { bg: '#27272a', color: '#a1a1aa', label: status };

  return (
    <span
      style={{
        fontSize: '0.75rem',
        padding: '0.125rem 0.375rem',
        borderRadius: 4,
        background: style.bg,
        color: style.color,
      }}
    >
      {style.label}
    </span>
  );
}
