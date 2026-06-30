import { evidenceTypeLabel } from "../../constants/evidence";
import type { PlanEvidence } from "../../types/rnc8d";
import { formatDateTime } from "../../utils/format";
import { Modal } from "../ui/Modal";
import { formatEvidenceFileSize } from "./evidenceAttachmentUtils";
import { EvidencePreviewContent } from "./EvidencePreviewContent";
import { evidencePreviewTitle } from "./evidencePreviewUtils";

type Props = {
  planId: string;
  evidence: PlanEvidence | null;
  open: boolean;
  onClose: () => void;
};

export function EvidencePreviewModal({ planId, evidence, open, onClose }: Props) {
  return (
    <Modal
      open={open}
      title={evidence ? evidencePreviewTitle(evidence) : "Pré-visualização"}
      className="pac-modal--evidence-preview"
      onClose={onClose}
    >
      {evidence ? (
        <div className="pac-evidence-preview-modal">
          <EvidencePreviewContent planId={planId} evidence={evidence} />
          {evidence.description ? (
            <p className="pac-muted pac-evidence-preview-modal__description">
              {evidence.description}
            </p>
          ) : null}
          <div className="pac-evidence-preview-modal__meta">
            <span>{evidenceTypeLabel(evidence.type)}</span>
            <span>{formatEvidenceFileSize(evidence.size_bytes)}</span>
            <span>{formatDateTime(evidence.created_at)}</span>
          </div>
        </div>
      ) : null}
    </Modal>
  );
}
