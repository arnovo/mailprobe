'use client';

import { fetchWithAuth } from '@/lib/auth';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AlertsModalProps {
  data: {
    leadId: number;
    leadName: string;
    alerts: string[];
    firstName: string;
    lastName: string;
  } | null;
  workspaceId: string;
  onClose: () => void;
  onSaved: () => void;
}

export function AlertsModal({ data, workspaceId, onClose, onSaved }: AlertsModalProps) {
  const tCommon = useTranslations('common');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [saving, setSaving] = useState(false);

  const handleClose = useCallback(() => {
    setFirstName('');
    setLastName('');
    onClose();
  }, [onClose]);

  // Reset form when modal opens
  useEffect(() => {
    if (data) {
      setFirstName(data.firstName);
      setLastName(data.lastName);
    }
  }, [data]);

  // Handle Escape key
  useEffect(() => {
    if (!data) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [data, handleClose]);

  if (!data) return null;

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetchWithAuth(`${API_URL}/v1/leads/${data.leadId}`, {
        method: 'PATCH',
        headers: { 'X-Workspace-Id': workspaceId, 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_name: firstName.trim(), last_name: lastName.trim() }),
      });
      const result = await res.json();
      if (result.error) {
        alert(result.error.message || tCommon('errors.save'));
      } else {
        handleClose();
        onSaved();
      }
    } catch {
      alert(tCommon('errors.networkError'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      {/* Backdrop */}
      <button
        type="button"
        aria-label="Cerrar modal"
        onClick={handleClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.6)',
          border: 'none',
          cursor: 'pointer',
        }}
      />
      {/* Modal content */}
      <div
        role="document"
        style={{
          position: 'relative',
          background: '#1e293b',
          borderRadius: 8,
          padding: '1.5rem',
          maxWidth: 400,
          width: '90%',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Alertas: {data.leadName}</h3>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Cerrar"
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.25rem', lineHeight: 1 }}
          >
            ×
          </button>
        </div>
        <ul style={{ margin: '0 0 1rem 0', paddingLeft: '1.25rem', color: '#fbbf24' }}>
          {data.alerts.map((alert, i) => (
            <li key={i} style={{ marginBottom: '0.5rem' }}>{alert}</li>
          ))}
        </ul>
        <div style={{ borderTop: '1px solid #334155', paddingTop: '1rem' }}>
          <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#e2e8f0' }}>Editar lead</h4>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Nombre"
              aria-label="Nombre"
              style={{ flex: 1, padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0' }}
            />
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Apellido"
              aria-label="Apellido"
              style={{ flex: 1, padding: '0.5rem', background: '#0f172a', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0' }}
            />
          </div>
          <button
            type="button"
            disabled={saving}
            onClick={handleSave}
            style={{ padding: '0.5rem 1rem', cursor: saving ? 'not-allowed' : 'pointer' }}
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  );
}
