import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { fetchWithAuth } from '@/lib/auth';
import { useLeads } from '@/hooks/useLeads';
import { createLead } from '@/__tests__/factories/lead';

vi.mock('@/lib/auth', () => ({
  fetchWithAuth: vi.fn(),
}));

function TestWrapper() {
  const { leads, loading, error } = useLeads({
    token: 'test-token',
    workspaceId: 'ws-1',
  });
  if (loading) return <span data-testid="loading">Loading</span>;
  if (error) return <span data-testid="error">{error}</span>;
  return (
    <ul data-testid="leads-list">
      {leads.map((l) => (
        <li key={l.id}>{l.email_best}</li>
      ))}
    </ul>
  );
}

describe('useLeads', () => {
  beforeEach(() => {
    vi.mocked(fetchWithAuth).mockReset();
    const lead = createLead({ id: 1, email_best: 'test@example.com' });
    vi.mocked(fetchWithAuth).mockResolvedValue(
      new Response(
        JSON.stringify({
          data: { items: [lead] },
        })
      )
    );
  });

  it('loads leads and shows one item with no error', async () => {
    render(<TestWrapper />);
    expect(screen.getByTestId('loading')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('leads-list')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    expect(screen.queryByTestId('error')).not.toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(fetchWithAuth).toHaveBeenCalled();
  });
});
