import { FilePreviewModal } from "@delpi/plugin-ui/index";

import { evidenceTypeLabel } from "../../constants/evidence";
import type { PlanEvidence } from "../../types/rnc8d";
import { formatDateTime } from "../../utils/format";
import { formatEvidenceFileSize } from "./evidenceAttachmentUtils";
import { evidencePreviewTitle } from "./evidencePreviewUtils";
import { usePlanEvidencePreviewState } from "./usePlanEvidencePreviewState";

type Props = {
  planId: string;
  evidence: PlanEvidence | null;
  open: boolean;
  onClose: () => void;
};

export function EvidencePreviewModal({ planId, evidence, open, onClose }: Props) {
  const { mode, blobSource, previewState } = usePlanEvidencePreviewState(planId, evidence);
  const title = evidence ? evidencePreviewTitle(evidence) : "Pré-visualização";

  return (
    <FilePreviewModal
      open={open}
      title={title}
      onClose={onClose}
      source={blobSource}
      previewState={previewState}
      mimeType={evidence?.mime_type}
      fileName={evidence?.file_name}
      declaredType={evidence?.type}
      enabled={mode !== "none"}
      portalScopeClassName="dashboard-quality-action-plans"
      afterPreview={
        evidence?.description ? (
          <p className="delpi-ui-file-preview__description">{evidence.description}</p>
        ) : null
      }
      metaItems={
        evidence
          ? [
              evidenceTypeLabel(evidence.type),
              formatEvidenceFileSize(evidence.size_bytes),
              formatDateTime(evidence.created_at),
            ]
          : undefined
      }
    />
  );
}
