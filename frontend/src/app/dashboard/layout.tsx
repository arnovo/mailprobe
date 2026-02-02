'use client';

/**
 * Layout del dashboard: navegación común y selector de workspace.
 * Solo se muestra tras comprobar auth en el cliente (evita hydration mismatch).
 * Usa fetchWithAuth: en 401 intenta refresh; si falla, redirige a /login.
 */

import { fetchWithAuth, getAccessToken } from '@/lib/auth';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  // Montado en cliente: true solo después del primer useEffect (evita leer localStorage en SSR)
  const [mounted, setMounted] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [workspaceId, setWorkspaceId] = useState('1');
  const [workspaces, setWorkspaces] = useState<{ id: number; name: string; slug: string }[]>([]);

  // Al montar: leer token y workspace_id; escuchar actualización tras refresh
  useEffect(() => {
    setToken(getAccessToken());
    const wid = typeof window !== 'undefined' ? localStorage.getItem('workspace_id') : null;
    if (wid) setWorkspaceId(wid);
    setMounted(true);
    const onTokenUpdated = () => setToken(getAccessToken());
    window.addEventListener('auth-token-updated', onTokenUpdated);
    return () => window.removeEventListener('auth-token-updated', onTokenUpdated);
  }, []);

  // Cuando ya estamos montados y hay token: cargar lista de workspaces (fetchWithAuth hace refresh si 401)
  useEffect(() => {
    if (!mounted || !token) return;
    fetchWithAuth(`${API_URL}/v1/workspaces`)
      .then((r) => r.json())
      .then((d) => {
        if (d.data?.items?.length) {
          setWorkspaces(d.data.items);
          const wid = localStorage.getItem('workspace_id') || String(d.data.items[0].id);
          setWorkspaceId(wid);
          localStorage.setItem('workspace_id', wid);
        }
      })
      .catch(() => {});
  }, [mounted, token]);

  // Si estamos montados y no hay token: redirigir a login
  useEffect(() => {
    if (mounted && !token) window.location.href = '/login';
  }, [mounted, token]);

  const handleWorkspaceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value;
    setWorkspaceId(v);
    localStorage.setItem('workspace_id', v);
  };

  // Mismo HTML en servidor y cliente hasta que mounted: evita error de hydration
  if (!mounted) {
    return (
      <div className="container">
        <p>Cargando...</p>
      </div>
    );
  }
  if (!token) return null;

  const navLink = (href: string, label: string) => (
    <Link
      href={href}
      className={pathname === href ? 'nav-active' : ''}
      style={{ padding: '0.5rem', fontWeight: pathname === href ? 600 : undefined }}
    >
      {label}
    </Link>
  );

  return (
    <div className="container">
      <h1 style={{ marginBottom: '0.5rem' }}>Mailprobe</h1>
      <nav style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #334155' }}>
        {navLink('/dashboard', 'Leads')}
        {navLink('/dashboard/jobs', 'Jobs')}
        {navLink('/dashboard/config', 'Configuración')}
        {navLink('/dashboard/api-keys', 'API Keys')}
        {navLink('/dashboard/webhooks', 'Webhooks')}
        {navLink('/dashboard/exports', 'Exports')}
        {navLink('/dashboard/usage', 'Uso')}
        <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Workspace:
          {workspaces.length > 0 ? (
            <select value={workspaceId} onChange={handleWorkspaceChange} style={{ minWidth: 160 }}>
              {workspaces.map((w) => (
                <option key={w.id} value={String(w.id)}>{w.name}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={workspaceId}
              onChange={(e) => {
                const v = e.target.value;
                setWorkspaceId(v);
                localStorage.setItem('workspace_id', v);
              }}
              style={{ width: 60 }}
              placeholder="ID"
            />
          )}
        </span>
      </nav>
      {children}
    </div>
  );
}
