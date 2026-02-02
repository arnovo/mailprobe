'use client';

/**
 * Página de login: email + contraseña.
 * Llama a POST /v1/auth/login; si OK guarda access_token y refresh_token en localStorage
 * y redirige al dashboard.
 */

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function LoginPage() {
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
      setError(data.error.message || 'Error al iniciar sesión');
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
      <h1>Iniciar sesión</h1>
      <form onSubmit={handleSubmit} style={{ maxWidth: 400, marginTop: '1rem' }}>
        {error && <p style={{ color: '#f87171', marginBottom: '0.5rem' }}>{error}</p>}
        <div style={{ marginBottom: '0.75rem' }}>
          <label htmlFor="login-email" style={{ display: 'block', marginBottom: '0.25rem' }}>Email</label>
          <input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ width: '100%' }} />
        </div>
        <div style={{ marginBottom: '0.75rem' }}>
          <label htmlFor="login-password" style={{ display: 'block', marginBottom: '0.25rem' }}>Contraseña</label>
          <input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ width: '100%' }} />
        </div>
        <button type="submit">Entrar</button>
      </form>
      <p style={{ marginTop: '1rem' }}>
        <Link href="/register">Crear cuenta</Link>
      </p>
    </div>
  );
}
