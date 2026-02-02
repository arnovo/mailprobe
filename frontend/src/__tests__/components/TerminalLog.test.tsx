import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TerminalLog } from '@/components/ui/TerminalLog';

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}));

describe('TerminalLog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when lines is empty', () => {
    const { container: _container } = render(<TerminalLog lines={[]} />);
    expect(_container.querySelector('.terminal-log')).toBeNull();
  });

  it('renders both lines when given plain text', () => {
    render(<TerminalLog lines={['a', 'Error: b']} />);
    expect(screen.getByText('a')).toBeInTheDocument();
    expect(screen.getByText('Error: b')).toBeInTheDocument();
  });

  it('applies error styling to line containing "Error"', () => {
    render(<TerminalLog lines={['a', 'Error: b']} />);
    const errorSpan = screen.getByText('Error: b');
    expect(errorSpan).toHaveStyle({ color: 'rgb(248, 81, 73)' });
  });

  it('renders normal line with default color', () => {
    render(<TerminalLog lines={['normal line']} />);
    const normalSpan = screen.getByText('normal line');
    expect(normalSpan).toHaveStyle({ color: 'rgb(126, 231, 135)' });
  });
});
