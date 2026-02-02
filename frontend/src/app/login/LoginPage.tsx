'use client';

/**
 * Login page: email + password.
 * Calls POST /v1/auth/login; if OK saves access_token and refresh_token to localStorage
 * and redirects to dashboard.
 */

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function LoginPage() {
  const t = useTranslations('auth');
  const tErrors = useTranslations('errors');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (data.error) {
      // Try to get translated error, fallback to API message
      const errorCode = data.error.code;
      const translatedError = errorCode ? tErrors(errorCode as never) : null;
      setError(translatedError || data.error.message || t('invalidCredentials'));
      return;
    }
    if (data.data?.access_token) {
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', data.data.access_token);
        localStorage.setItem('refresh_token', data.data.refresh_token || '');
      }
      router.push('/dashboard');
    }
  }

  return (
    <div className="container">
      <h1>{t('login')}</h1>
      <form onSubmit={handleSubmit} style={{ maxWidth: 400, marginTop: '1rem' }}>
        {error && <p style={{ color: '#f87171', marginBottom: '0.5rem' }}>{error}</p>}
        <div style={{ marginBottom: '0.75rem' }}>
          <label htmlFor="login-email" style={{ display: 'block', marginBottom: '0.25rem' }}>{t('email')}</label>
          <input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ width: '100%' }} />
        </div>
        <div style={{ marginBottom: '0.75rem' }}>
          <label htmlFor="login-password" style={{ display: 'block', marginBottom: '0.25rem' }}>{t('password')}</label>
          <input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ width: '100%' }} />
        </div>
        <button type="submit">{t('login')}</button>
      </form>
      <p style={{ marginTop: '1rem' }}>
        <Link href="/register">{t('register')}</Link>
      </p>
    </div>
  );
}
