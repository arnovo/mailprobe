'use client';

import { CancelButton, LogContent, Modal, NavButtons } from '@/components/ui';
import { Job, useJobLog } from '@/hooks';
import { useCallback } from 'react';

interface JobLogModalProps {
  job: Job | null;
  allJobs: Job[];
  workspaceId: string;
  cancellingId: string | null;
  onClose: () => void;
  onCancel: (jobId: string) => void;
  onNavigate: (job: Job) => void;
}

export function JobLogModal({ job, allJobs, workspaceId, cancellingId, onClose, onCancel, onNavigate }: JobLogModalProps) {
  const { lines, entries, status, loading, error, cleanup } = useJobLog(job?.job_id ?? null, workspaceId);

  const relatedJobs = job?.lead_id ? allJobs.filter((j) => j.lead_id === job.lead_id) : [];
  const currentIndex = job ? relatedJobs.findIndex((j) => j.job_id === job.job_id) : -1;

  const handleClose = useCallback(() => {
    cleanup();
    onClose();
  }, [cleanup, onClose]);

  const navigate = (direction: 'prev' | 'next') => {
    const newIdx = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
    if (newIdx >= 0 && newIdx < relatedJobs.length) onNavigate(relatedJobs[newIdx]);
  };

  const showCancel = !!(job && (status === 'queued' || status === 'running'));
  const title = job
    ? `Log — ${job.kind} (${job.job_id.slice(0, 8)}…)${relatedJobs.length > 1 ? ` ${currentIndex + 1}/${relatedJobs.length}` : ''}`
    : 'Log';

  return (
    <Modal
      open={!!job}
      onClose={handleClose}
      title={title}
      titleExtra={<NavButtons currentIndex={currentIndex} total={relatedJobs.length} onNavigate={navigate} />}
      headerActions={<CancelButton show={showCancel} cancelling={cancellingId === job?.job_id} onClick={() => job && onCancel(job.job_id)} />}
      maxWidth={640}
    >
      <LogContent
        loading={loading}
        error={error}
        status={status}
        entries={entries}
        lines={lines}
        emptyMessage="No hay líneas de log para este job."
      />
    </Modal>
  );
}
