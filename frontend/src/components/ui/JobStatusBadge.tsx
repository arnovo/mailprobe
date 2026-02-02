'use client';

import { useTranslations } from 'next-intl';

interface JobStatusBadgeProps {
  status: string | null;
}

const STATUS_STYLES: Record<string, { bg: string; color: string }> = {
  succeeded: { bg: '#14532d', color: '#4ade80' },
  failed: { bg: '#7f1d1d', color: '#fca5a5' },
  cancelled: { bg: '#78350f', color: '#fcd34d' },
  running: { bg: '#1e3a5f', color: '#93c5fd' },
  queued: { bg: '#3f3f46', color: '#a1a1aa' },
};

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const t = useTranslations('jobs.status');

  if (!status) {
    return <span style={{ color: '#64748b', fontSize: '0.75rem' }}>—</span>;
  }

  const style = STATUS_STYLES[status] || { bg: '#27272a', color: '#a1a1aa' };
  const label = t(status as never) || status;

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
      {label}
    </span>
  );
}
