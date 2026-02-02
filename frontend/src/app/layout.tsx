/**
 * Layout raíz de la app Next.js (App Router).
 * Envuelve todas las páginas; aquí se importan estilos globales y metadatos.
 */

import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Mailprobe',
  description: 'B2B email finder and verifier',
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
