'use client';

import { CONFIG_CONSTANTS } from '@/hooks/useConfig';
import { CustomPatternEditor } from './CustomPatternEditor';

const { MIN_PATTERNS } = CONFIG_CONSTANTS;

interface PatternSettingsProps {
  enabledIndices: number[];
  patternLabels: string[];
  allowNoLastname: boolean;
  customPatterns: string[];
  onTogglePattern: (index: number) => void;
  onAllowNoLastnameChange: (v: boolean) => void;
  onCustomPatternsChange: (patterns: string[]) => void;
}

export function PatternSettings({
  enabledIndices,
  patternLabels,
  allowNoLastname,
  customPatterns,
  onTogglePattern,
  onAllowNoLastnameChange,
  onCustomPatternsChange,
}: PatternSettingsProps) {
  const labels = patternLabels.length ? patternLabels : Array.from({ length: 10 }, (_, i) => `Patrón ${i + 1}`);

  return (
    <>
      <div>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: '#e2e8f0' }}>
          <input
            type="checkbox"
            checked={allowNoLastname}
            onChange={(e) => onAllowNoLastnameChange(e.target.checked)}
          />
          Permitir leads sin apellido
        </label>
        <p style={{ marginTop: '0.25rem', color: '#94a3b8', fontSize: '0.75rem', marginLeft: '1.5rem' }}>
          Si está activado, genera candidatos genéricos (info@, contact@, contacto@, etc.) cuando el lead no tiene apellido.
        </p>
      </div>

      <div>
        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#e2e8f0' }}>
          Patrones estándar ({enabledIndices.length} de {labels.length} habilitados; mínimo {MIN_PATTERNS})
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {labels.map((label, i) => (
            <label key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={enabledIndices.includes(i)}
                onChange={() => onTogglePattern(i)}
              />
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.875rem', color: '#e2e8f0' }}>
                {label}
              </span>
            </label>
          ))}
        </div>
        {enabledIndices.length < MIN_PATTERNS && enabledIndices.length > 0 && (
          <p style={{ color: '#fbbf24', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Activa al menos {MIN_PATTERNS - enabledIndices.length} más para guardar.
          </p>
        )}
      </div>

      <CustomPatternEditor patterns={customPatterns} onChange={onCustomPatternsChange} />
    </>
  );
}
