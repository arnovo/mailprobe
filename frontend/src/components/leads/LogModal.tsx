'use client';

import { CancelButton, LogContent, Modal, NavButtons } from '@/components/ui';
import { useLogModal } from '@/hooks';

interface LogModalProps {
  lead: { id: number; name: string } | null;
  workspaceId: string;
  onClose: () => void;
}

export function LogModal({ lead, workspaceId, onClose }: LogModalProps) {
  const state = useLogModal(lead, workspaceId);

  const handleClose = () => {
    state.cleanup();
    onClose();
  };

  const showCancel = (state.status === 'queued' || state.status === 'running') && !!state.jobId;
  const title = `Log — ${lead?.name || ''}${state.jobs.length > 1 ? ` (${state.jobIndex + 1}/${state.jobs.length})` : ''}`;

  return (
    <Modal
      open={!!lead}
      onClose={handleClose}
      title={title}
      titleExtra={<NavButtons currentIndex={state.jobIndex} total={state.jobs.length} onNavigate={state.navigate} />}
      headerActions={<CancelButton show={showCancel} cancelling={state.cancelling} onClick={state.handleCancel} />}
    >
      <LogContent
        loading={state.loading}
        error={state.error}
        status={state.status}
        entries={state.entries}
        lines={state.lines}
        inProgressMessage="Job en curso. El log se actualizará automáticamente."
      />
    </Modal>
  );
}
