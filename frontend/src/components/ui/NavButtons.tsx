'use client';

interface NavButtonsProps {
  currentIndex: number;
  total: number;
  onNavigate: (direction: 'prev' | 'next') => void;
}

export function NavButtons({ currentIndex, total, onNavigate }: NavButtonsProps) {
  if (total <= 1) return null;
  
  const btnStyle = (disabled: boolean) => ({
    background: disabled ? '#1e293b' : '#334155',
    border: 'none',
    color: disabled ? '#475569' : '#e2e8f0',
    cursor: disabled ? 'not-allowed' : 'pointer',
    borderRadius: 4,
    padding: '0.25rem 0.5rem',
    fontSize: '0.875rem',
  });
  
  return (
    <div style={{ display: 'flex', gap: '0.25rem', flexShrink: 0 }}>
      <button
        type="button"
        onClick={() => onNavigate('prev')}
        disabled={currentIndex <= 0}
        style={btnStyle(currentIndex <= 0)}
        aria-label="Anterior"
      >
        ◀
      </button>
      <button
        type="button"
        onClick={() => onNavigate('next')}
        disabled={currentIndex >= total - 1}
        style={btnStyle(currentIndex >= total - 1)}
        aria-label="Siguiente"
      >
        ▶
      </button>
    </div>
  );
}
