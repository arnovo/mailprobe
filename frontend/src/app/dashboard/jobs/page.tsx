'use client';

/**
 * Página Jobs: lista jobs del workspace (activos por defecto).
 * Refactorizado para usar componentes modulares y hooks personalizados.
 */

import { JobLogModal, JobsTable } from '@/components/jobs';
import { Job, useAuth, useJobs } from '@/hooks';
import { useState } from 'react';

export default function JobsPage() {
  const { token, workspaceId } = useAuth();
  const [activeOnly, setActiveOnly] = useState(false);
  const { jobs, loading, error, cancellingId, cancelError, cancelJob } = useJobs({ 
    token, 
    workspaceId, 
    activeOnly 
  });
  const [logModalJob, setLogModalJob] = useState<Job | null>(null);

  if (!token) {
    return <div className="card"><p>Cargando...</p></div>;
  }

  return (
    <div className="card">
      <h2>Jobs del workspace</h2>
      <p style={{ color: '#94a3b8', marginBottom: '0.5rem' }}>
        Jobs de verificación, export, etc. Desmarca &quot;Solo activos&quot; para ver también completados, fallidos y cancelados (y su log).
      </p>
      
      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          type="checkbox"
          checked={activeOnly}
          onChange={(e) => setActiveOnly(e.target.checked)}
        />
        Solo activos (queued / running)
      </label>

      {cancelError && (
        <p style={{ color: '#f87171', marginBottom: '0.5rem' }}>{cancelError}</p>
      )}

      {loading ? (
        <p>Cargando...</p>
      ) : error ? (
        <p style={{ color: '#f87171' }}>{error}</p>
      ) : jobs.length === 0 ? (
        <p>No hay jobs{activeOnly ? ' activos' : ''}.</p>
      ) : (
        <JobsTable
          jobs={jobs}
          cancellingId={cancellingId}
          onViewLog={setLogModalJob}
          onCancel={cancelJob}
        />
      )}

      <JobLogModal
        job={logModalJob}
        allJobs={jobs}
        workspaceId={workspaceId}
        cancellingId={cancellingId}
        onClose={() => setLogModalJob(null)}
        onCancel={cancelJob}
        onNavigate={setLogModalJob}
      />
    </div>
  );
}
