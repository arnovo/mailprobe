'use client';

import { useState } from 'react';

const MAX_CUSTOM_PATTERNS = 20;
const MAX_PATTERN_LENGTH = 100;

interface CustomPatternEditorProps {
  patterns: string[];
  onChange: (patterns: string[]) => void;
}

export function CustomPatternEditor({ patterns, onChange }: CustomPatternEditorProps) {
  const [newPattern, setNewPattern] = useState('');
  const [error, setError] = useState('');

  const validatePattern = (pattern: string): string | null => {
    if (!pattern.trim()) return 'El patrón no puede estar vacío';
    if (!pattern.includes('@{domain}')) return 'El patrón debe contener @{domain}';
    if (pattern.length > MAX_PATTERN_LENGTH) return 'El patrón es demasiado largo (máx. 100 caracteres)';
    if (patterns.includes(pattern.trim())) return 'Este patrón ya existe';
    return null;
  };

  const addPattern = () => {
    const pattern = newPattern.trim();
    const validationError = validatePattern(pattern);
    if (validationError) {
      setError(validationError);
      return;
    }
    if (patterns.length >= MAX_CUSTOM_PATTERNS) {
      setError(`Máximo ${MAX_CUSTOM_PATTERNS} patrones personalizados`);
      return;
    }
    onChange([...patterns, pattern]);
    setNewPattern('');
    setError('');
  };

  const removePattern = (index: number) => {
    onChange(patterns.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addPattern();
    }
  };

  const codeStyle = { background: '#334155', padding: '0.125rem 0.25rem', borderRadius: 3 };

  return (
    <div style={{ marginTop: '1rem' }}>
      <label style={{ display: 'block', marginBottom: '0.5rem', color: '#e2e8f0' }}>
        Patrones personalizados ({patterns.length}/{MAX_CUSTOM_PATTERNS})
      </label>
      <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginBottom: '0.75rem' }}>
        Añade patrones adicionales usando: <code style={codeStyle}>{'{first}'}</code> (nombre), 
        <code style={{ ...codeStyle, marginLeft: '0.25rem' }}>{'{last}'}</code> (apellido), 
        <code style={{ ...codeStyle, marginLeft: '0.25rem' }}>{'{f}'}</code> (inicial nombre), 
        <code style={{ ...codeStyle, marginLeft: '0.25rem' }}>{'{l}'}</code> (inicial apellido), 
        <code style={{ ...codeStyle, marginLeft: '0.25rem' }}>{'{domain}'}</code> (dominio).
        Ejemplo: <code style={codeStyle}>{'{first}.{l}@{domain}'}</code>
      </p>

      {/* Lista de patrones */}
      {patterns.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', marginBottom: '0.75rem' }}>
          {patterns.map((pattern, i) => (
            <div 
              key={i} 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                background: '#1e293b',
                padding: '0.375rem 0.5rem',
                borderRadius: 4,
              }}
            >
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.875rem', color: '#4ade80', flex: 1 }}>
                {pattern}
              </span>
              <button
                type="button"
                onClick={() => removePattern(i)}
                style={{ 
                  background: 'transparent', 
                  border: 'none', 
                  color: '#f87171', 
                  cursor: 'pointer',
                  padding: '0.125rem 0.375rem',
                  fontSize: '0.875rem',
                }}
                title="Eliminar patrón"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input para nuevo patrón */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <input
            type="text"
            value={newPattern}
            onChange={(e) => { setNewPattern(e.target.value); setError(''); }}
            onKeyDown={handleKeyDown}
            placeholder="{first}.{last}@{domain}"
            style={{ 
              width: '100%',
              fontFamily: 'ui-monospace, monospace',
              fontSize: '0.875rem',
            }}
            disabled={patterns.length >= MAX_CUSTOM_PATTERNS}
          />
          {error && (
            <p style={{ color: '#f87171', fontSize: '0.75rem', marginTop: '0.25rem' }}>
              {error}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={addPattern}
          disabled={patterns.length >= MAX_CUSTOM_PATTERNS}
          style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap' }}
        >
          Añadir
        </button>
      </div>
    </div>
  );
}
