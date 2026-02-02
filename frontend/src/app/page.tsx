'use client';

/**
 * Página de inicio (/) antes de iniciar sesión.
 * Enlaces a login, registro y dashboard; muestra base URL de la API.
 */

import Link from 'next/link';

export default function Home() {
  return (
    <div className="container">
      <h1>Mailprobe</h1>
      <p style={{ marginTop: '0.5rem', color: '#94a3b8' }}>
        B2B email finder y verificación. Multi-tenant, listo para n8n.
      </p>
      <nav>
        <Link href="/login">Iniciar sesión</Link>
        <Link href="/register">Registro</Link>
        <Link href="/dashboard">Dashboard</Link>
      </nav>
      <div className="card">
        <h2>API v1</h2>
        <p>Base URL: <code>{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1</code></p>
        <p>Autenticación: Bearer JWT o header <code>X-API-Key</code>. Workspace: <code>X-Workspace-Id</code>.</p>
        <p>Ver <a href="/docs" target="_blank" rel="noopener">/docs</a> (Swagger) en el backend.</p>
      </div>
    </div>
  );
}
