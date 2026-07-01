import { actionTypeLabel } from "../constants/actionPlans";
import type { PlanAction } from "../types/actionPlan";
import type { MyQueueItem } from "../types/myQueue";
import { EvidenceAttachForm } from "./evidence/EvidenceAttachForm";
import { Modal } from "./ui/Modal";

type Props = {
  item: MyQueueItem | null;
  open: boolean;
  onClose: () => void;
  onUploaded: () => void | Promise<void>;
};

function queueItemAsAction(item: MyQueueItem): PlanAction {
  return {
    id: item.action_id,
    action_type: item.action_type,
    description: item.description,
    responsible_user_id: item.responsible_user_id ?? undefined,
    responsible_name: item.responsible_name ?? undefined,
    department: item.department ?? undefined,
    due_date: item.due_date ?? undefined,
    status: item.action_status,
    evidence_required: item.evidence_required,
    completed_at: item.completed_at ?? undefined,
  };
}

export function MyQueueEvidenceModal({ item, open, onClose, onUploaded }: Props) {
  return (
    <Modal
      open={open}
      title="Anexar evidência à ação"
      className="pac-modal--my-queue-evidence pac-modal--evidence"
      onClose={onClose}
    >
      {item ? (
        <div className="pac-my-queue-evidence-modal">
          <div className="pac-my-queue-evidence-modal__context">
            <div className="pac-my-queue-evidence-modal__context-head">
              <strong>{item.plan_code ?? item.plan_id}</strong>
              <span className="pac-my-queue-evidence-modal__action-type">
                {actionTypeLabel(item.action_type)}
              </span>
            </div>
            <p className="pac-my-queue-evidence-modal__context-text">{item.description}</p>
          </div>
          <EvidenceAttachForm
            planId={item.plan_id}
            actions={[queueItemAsAction(item)]}
            defaultSection="corrective"
            defaultActionId={item.action_id}
            lockActionId
            showFooter
            onClose={onClose}
            onUploaded={async () => {
              await onUploaded();
              onClose();
            }}
          />
        </div>
      ) : null}
    </Modal>
  );
}
