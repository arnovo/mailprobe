'use client';

import type { LogEntry } from '@/types';
import { LogTable } from './LogTable';
import { StatusText } from './StatusText';
import { TerminalLog } from './TerminalLog';

interface LogContentProps {
  loading: boolean;
  error: string | null;
  status: string | null;
  entries: LogEntry[];
  lines: string[];
  emptyMessage?: string;
  inProgressMessage?: string;
}

export function LogContent({
  loading,
  error,
  status,
  entries,
  lines,
  emptyMessage = 'No hay líneas de log.',
  inProgressMessage = 'Job en curso. El log se actualizará automáticamente.',
}: LogContentProps) {
  const isInProgress = status === 'running' || status === 'queued';
  const isEmpty = entries.length === 0 && lines.length === 0;

  return (
    <>
      {loading && <p style={{ color: '#94a3b8' }}>Cargando...</p>}
      {error && !loading && <p style={{ color: '#f87171', marginBottom: '0.75rem' }}>{error}</p>}
      <StatusText status={status} loading={loading} />
      {!loading && <LogTable entries={entries} />}
      {entries.length === 0 && lines.length > 0 && !loading && (
        <TerminalLog lines={lines} maxHeight={320} aria-label="Log" />
      )}
      {!loading && isEmpty && !error && (
        <p style={{ color: '#94a3b8' }}>
          {isInProgress ? inProgressMessage : emptyMessage}
        </p>
      )}
    </>
  );
}
