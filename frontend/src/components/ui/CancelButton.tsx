'use client';

interface CancelButtonProps {
  show: boolean;
  cancelling: boolean;
  onClick: () => void;
}

export function CancelButton({ show, cancelling, onClick }: CancelButtonProps) {
  if (!show) return null;
  
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={cancelling}
      style={{
        background: '#7f1d1d',
        border: 'none',
        color: '#fca5a5',
        cursor: cancelling ? 'not-allowed' : 'pointer',
        borderRadius: 4,
        padding: '0.25rem 0.5rem',
        fontSize: '0.8125rem',
      }}
    >
      {cancelling ? 'Cancelando…' : 'Cancelar'}
    </button>
  );
}
