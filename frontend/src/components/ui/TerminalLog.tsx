'use client';

interface TerminalLogProps {
  lines: string[];
  maxHeight?: number;
  'aria-label'?: string;
}

export function TerminalLog({ lines, maxHeight = 220, 'aria-label': ariaLabel = 'Log' }: TerminalLogProps) {
  if (lines.length === 0) return null;

  return (
    <div
      className="terminal-log"
      style={{
        background: '#0d1117',
        border: '1px solid #30363d',
        borderRadius: '0.5rem',
        padding: '1rem',
        fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
        fontSize: '0.8125rem',
        color: '#7ee787',
        overflow: 'auto',
        maxHeight,
        userSelect: 'text',
        cursor: 'default',
      }}
      role="log"
      aria-label={ariaLabel}
    >
      {lines.map((line, i) => (
        <div key={i} style={{ marginBottom: line.startsWith('Error') ? 0 : '0.25rem' }}>
          <span style={{ color: '#8b949e', marginRight: '0.5rem' }}>&gt;</span>
          <span style={{ color: line.startsWith('Error') ? '#f85149' : '#7ee787' }}>{line}</span>
        </div>
      ))}
    </div>
  );
}
