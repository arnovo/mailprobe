'use client';

import { useTranslations } from 'next-intl';

interface LogMessage {
  code?: string;
  params?: Record<string, string | number>;
}

function parseLogLine(line: string): LogMessage | null {
  try {
    const parsed = JSON.parse(line);
    if (typeof parsed === 'object' && parsed !== null && 'code' in parsed) {
      return parsed as LogMessage;
    }
  } catch {
    // Not JSON, return null
  }
  return null;
}

interface TerminalLogProps {
  lines: string[];
  maxHeight?: number;
  'aria-label'?: string;
}

export function TerminalLog({ lines, maxHeight = 220, 'aria-label': ariaLabel = 'Log' }: TerminalLogProps) {
  const t = useTranslations('logs');

  if (lines.length === 0) return null;

  const translateLine = (line: string): string => {
    const parsed = parseLogLine(line);
    if (parsed?.code) {
      try {
        // Try to translate using the code
        return t(parsed.code, parsed.params || {});
      } catch {
        // If translation key doesn't exist, return raw line
        return line;
      }
    }
    // Not a JSON log message, return as-is
    return line;
  };

  const isErrorLine = (line: string): boolean => {
    const parsed = parseLogLine(line);
    if (parsed?.code) {
      return parsed.code.startsWith('ERROR_') || parsed.code === 'JOB_FAILED' || parsed.code === 'JOB_TIMEOUT';
    }
    return line.toLowerCase().includes('error');
  };

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
      {lines.map((line, i) => {
        const translatedLine = translateLine(line);
        const isError = isErrorLine(line);
        return (
          <div key={i} style={{ marginBottom: isError ? 0 : '0.25rem' }}>
            <span style={{ color: '#8b949e', marginRight: '0.5rem' }}>&gt;</span>
            <span style={{ color: isError ? '#f85149' : '#7ee787' }}>{translatedLine}</span>
          </div>
        );
      })}
    </div>
  );
}
