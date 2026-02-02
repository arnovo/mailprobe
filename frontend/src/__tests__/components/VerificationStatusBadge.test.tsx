import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VerificationStatusBadge } from '@/components/ui/VerificationStatusBadge';

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}));

describe('VerificationStatusBadge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders pending status', () => {
    render(<VerificationStatusBadge status="pending" />);
    expect(screen.getByText('status.pending')).toBeInTheDocument();
  });

  it('renders valid status', () => {
    render(<VerificationStatusBadge status="valid" />);
    expect(screen.getByText(/status\.valid/)).toBeInTheDocument();
  });

  it('renders invalid status', () => {
    render(<VerificationStatusBadge status="invalid" />);
    expect(screen.getByText(/status\.invalid/)).toBeInTheDocument();
  });

  it('renders risky status', () => {
    render(<VerificationStatusBadge status="risky" />);
    expect(screen.getByText(/status\.risky/)).toBeInTheDocument();
  });

  it('renders unknown status', () => {
    render(<VerificationStatusBadge status="unknown" />);
    expect(screen.getByText(/status\.unknown/)).toBeInTheDocument();
  });

  it('valid status has visible label', () => {
    render(<VerificationStatusBadge status="valid" />);
    expect(screen.getByText(/status\.valid/)).toBeVisible();
  });

  it('invalid status has visible label', () => {
    render(<VerificationStatusBadge status="invalid" />);
    expect(screen.getByText(/status\.invalid/)).toBeVisible();
  });
});
