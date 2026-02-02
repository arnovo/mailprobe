'use client';

/**
 * Jobs page: list workspace jobs (active by default).
 * Refactored to use modular components and custom hooks.
 */

import { useTranslations } from 'next-intl';
import { JobLogModal, JobsTable } from '@/components/jobs';
import { Job, useAuth, useJobs } from '@/hooks';
import { useState } from 'react';

export default function JobsPage() {
  const t = useTranslations('jobs');
  const tCommon = useTranslations('common');
  const { token, workspaceId } = useAuth();
  const [activeOnly, setActiveOnly] = useState(false);
  const { jobs, loading, error, cancellingId, cancelError, cancelJob } = useJobs({ 
    token, 
    workspaceId, 
    activeOnly 
  });
  const [logModalJob, setLogModalJob] = useState<Job | null>(null);

  if (!token) {
    return <div className="card"><p>{tCommon('loading')}</p></div>;
  }

  return (
    <div className="card">
      <h2>{t('title')}</h2>
      
      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          type="checkbox"
          checked={activeOnly}
          onChange={(e) => setActiveOnly(e.target.checked)}
        />
        {t('status.queued')} / {t('status.running')}
      </label>

      {cancelError && (
        <p style={{ color: '#f87171', marginBottom: '0.5rem' }}>{cancelError}</p>
      )}

      {loading ? (
        <p>{tCommon('loading')}</p>
      ) : error ? (
        <p style={{ color: '#f87171' }}>{error}</p>
      ) : jobs.length === 0 ? (
        <p>{t('noJobs')}</p>
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
