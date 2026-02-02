'use client';

interface LogEntry {
  created_at: string | null;
  message: string;
}

interface LogTableProps {
  entries: LogEntry[];
}

export function LogTable({ entries }: LogTableProps) {
  if (entries.length === 0) return null;
  
  return (
    <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', fontFamily: 'ui-monospace, monospace' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left' }}>
            <th style={{ padding: '0.5rem', color: '#94a3b8', whiteSpace: 'nowrap' }}>Hora</th>
            <th style={{ padding: '0.5rem', color: '#94a3b8' }}>Mensaje</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #334155' }}>
              <td style={{ padding: '0.5rem', color: '#64748b', whiteSpace: 'nowrap', verticalAlign: 'top' }}>
                {e.created_at ? new Date(e.created_at).toLocaleTimeString() : '—'}
              </td>
              <td style={{ padding: '0.5rem', color: e.message.startsWith('Error') ? '#f87171' : '#e2e8f0', wordBreak: 'break-word' }}>
                {e.message}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
