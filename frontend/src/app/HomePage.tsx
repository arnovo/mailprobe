'use client';

/**
 * Home page (/) before logging in.
 * Links to login, register, and dashboard; shows API base URL.
 */

import { useTranslations } from 'next-intl';
import Link from 'next/link';

export function HomePage() {
  const t = useTranslations('auth');
  const tNav = useTranslations('nav');

  return (
    <div className="container">
      <h1>Mailprobe</h1>
      <p style={{ marginTop: '0.5rem', color: '#94a3b8' }}>
        B2B email finder and verification. Multi-tenant, n8n ready.
      </p>
      <nav>
        <Link href="/login">{t('login')}</Link>
        <Link href="/register">{t('register')}</Link>
        <Link href="/dashboard">{tNav('dashboard')}</Link>
      </nav>
      <div className="card">
        <h2>API v1</h2>
        <p>Base URL: <code>{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1</code></p>
        <p>Auth: Bearer JWT or <code>X-API-Key</code> header. Workspace: <code>X-Workspace-Id</code>.</p>
        <p>See <a href="/docs" target="_blank" rel="noopener">/docs</a> (Swagger) on the backend.</p>
      </div>
    </div>
  );
}
