'use client';

import { Job } from '@/hooks/useJobs';
import { JobStatusBadge } from '@/components/ui';

const JOB_ID_DISPLAY_LENGTH = 8;

interface JobsTableProps {
  jobs: Job[];
  cancellingId: string | null;
  onViewLog: (job: Job) => void;
  onCancel: (jobId: string) => void;
}

export function JobsTable({ jobs, cancellingId, onViewLog, onCancel }: JobsTableProps) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left' }}>
            <th style={{ padding: '0.5rem' }}>Job ID</th>
            <th style={{ padding: '0.5rem' }}>Tipo</th>
            <th style={{ padding: '0.5rem' }}>Estado</th>
            <th style={{ padding: '0.5rem' }}>Progreso</th>
            <th style={{ padding: '0.5rem' }}>Lead ID</th>
            <th style={{ padding: '0.5rem' }}>Creado</th>
            <th style={{ padding: '0.5rem' }}></th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.job_id} style={{ borderBottom: '1px solid #334155' }}>
              <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                {job.job_id.slice(0, JOB_ID_DISPLAY_LENGTH)}…
              </td>
              <td style={{ padding: '0.5rem' }}>{job.kind}</td>
              <td style={{ padding: '0.5rem' }}>
                <JobStatusBadge status={job.status} />
              </td>
              <td style={{ padding: '0.5rem' }}>{job.progress}%</td>
              <td style={{ padding: '0.5rem' }}>{job.lead_id ?? '—'}</td>
              <td style={{ padding: '0.5rem', fontSize: '0.85rem' }}>
                {job.created_at ? new Date(job.created_at).toLocaleString() : '—'}
              </td>
              <td style={{ padding: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => onViewLog(job)}
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem' }}
                >
                  Ver log
                </button>
                {(job.status === 'queued' || job.status === 'running') && (
                  <button
                    type="button"
                    disabled={cancellingId === job.job_id}
                    onClick={() => onCancel(job.job_id)}
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem' }}
                  >
                    {cancellingId === job.job_id ? 'Cancelando…' : 'Cancelar'}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
