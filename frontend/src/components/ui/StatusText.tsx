'use client';

interface StatusTextProps {
  status: string | null;
  loading: boolean;
}

function getStatusColor(status: string): string {
  if (status === 'succeeded') return '#4ade80';
  if (status === 'failed') return '#f87171';
  if (status === 'cancelled') return '#fbbf24';
  return '#e2e8f0';
}

export function StatusText({ status, loading }: StatusTextProps) {
  if (!status || loading) return null;
  
  return (
    <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
      Estado: <strong style={{ color: getStatusColor(status) }}>{status}</strong>
    </p>
  );
}
