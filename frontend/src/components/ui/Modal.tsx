'use client';

import { ReactNode, useEffect } from 'react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  titleExtra?: ReactNode;
  headerActions?: ReactNode;
  children: ReactNode;
  maxWidth?: number;
}

export function Modal({ 
  open, 
  onClose, 
  title, 
  titleExtra,
  headerActions,
  children, 
  maxWidth = 560 
}: ModalProps) {
  // Handle Escape key
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      {/* Backdrop - using button for accessibility */}
      <button
        type="button"
        aria-label="Cerrar modal"
        onClick={onClose}
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
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '0.75rem',
          maxWidth,
          width: '100%',
          maxHeight: '85vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ 
          padding: '1rem 1.25rem', 
          borderBottom: '1px solid #334155', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          gap: '0.75rem' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: 0 }}>
            {titleExtra}
            <h3 
              id="modal-title" 
              style={{ 
                margin: 0, 
                fontSize: '1rem', 
                color: '#e2e8f0', 
                overflow: 'hidden', 
                textOverflow: 'ellipsis', 
                whiteSpace: 'nowrap' 
              }}
            >
              {title}
            </h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
            {headerActions}
            <button 
              type="button" 
              onClick={onClose} 
              aria-label="Cerrar" 
              style={{ 
                background: 'transparent', 
                border: 'none', 
                color: '#94a3b8', 
                cursor: 'pointer', 
                fontSize: '1.25rem', 
                lineHeight: 1 
              }}
            >
              &times;
            </button>
          </div>
        </div>
        <div style={{ padding: '1rem 1.25rem', overflow: 'auto', flex: 1 }}>
          {children}
        </div>
      </div>
    </div>
  );
}
