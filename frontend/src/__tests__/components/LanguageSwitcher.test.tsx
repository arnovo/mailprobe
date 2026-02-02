import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher';

const mockRefresh = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ refresh: mockRefresh }),
}));

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.cookie = '';
  });

  it('renders EN and ES buttons', () => {
    render(<LanguageSwitcher />);
    expect(screen.getByRole('button', { name: /EN/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ES/i })).toBeInTheDocument();
  });

  it('sets cookie and calls router.refresh when clicking a locale', async () => {
    const user = userEvent.setup();
    render(<LanguageSwitcher />);
    const enButton = screen.getByRole('button', { name: /EN/i });
    await user.click(enButton);
    expect(document.cookie).toContain('locale=en');
    expect(mockRefresh).toHaveBeenCalled();
  });

  it('sets locale=es when clicking ES', async () => {
    const user = userEvent.setup();
    render(<LanguageSwitcher />);
    const esButton = screen.getByRole('button', { name: /ES/i });
    await user.click(esButton);
    expect(document.cookie).toContain('locale=es');
    expect(mockRefresh).toHaveBeenCalled();
  });
});
