import { useEffect, useState } from "react";

import { updatePlanEvidence } from "../../api/actionPlansApi";
import type { PlanAction } from "../../types/actionPlan";
import type { PlanEvidence } from "../../types/rnc8d";
import { StateAlert } from "../StateAlert";
import { FormActions } from "../ui/FormActions";
import { Modal } from "../ui/Modal";
import { formatEvidenceFileSize } from "./evidenceAttachmentUtils";
import { EvidenceMetadataForm } from "./EvidenceMetadataForm";
import { PAC_GHOST_BTN } from "../ui/ghostChrome";

type Props = {
  planId: string;
  evidence: PlanEvidence | null;
  actions?: PlanAction[];
  open: boolean;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
};

export function EvidenceEditModal({
  planId,
  evidence,
  actions = [],
  open,
  onClose,
  onSaved,
}: Props) {
  const [evidenceType, setEvidenceType] = useState("image");
  const [section, setSection] = useState("general");
  const [actionId, setActionId] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!evidence || !open) return;
    setEvidenceType(evidence.type || "other");
    setSection(evidence.section ?? "general");
    setActionId(evidence.action_id ?? "");
    setDescription(evidence.description ?? "");
    setError(null);
  }, [evidence, open]);

  async function handleSave() {
    if (!evidence) return;
    setSaving(true);
    setError(null);
    try {
      await updatePlanEvidence(planId, evidence.id, {
        evidenceType,
        section,
        actionId: actionId || null,
        description: description.trim() || null,
      });
      await onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar evidência.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      title="Editar evidência"
      className="pac-modal--evidence-edit pac-modal--evidence"
      onClose={() => {
        if (!saving) onClose();
      }}
    >
      {evidence ? (
        <div className="pac-evidence-edit-modal">
          <div className="pac-evidence-edit-modal__file-card">
            <p className="pac-evidence-edit-modal__file-name">
              {evidence.file_name ?? evidence.id}
            </p>
            <p className="pac-evidence-edit-modal__file-size">
              {formatEvidenceFileSize(evidence.size_bytes)}
            </p>
          </div>
          {error ? <StateAlert variant="error">{error}</StateAlert> : null}
          <EvidenceMetadataForm
            idPrefix={`edit-${evidence.id}`}
            evidenceType={evidenceType}
            section={section}
            actionId={actionId}
            description={description}
            actions={actions}
            disabled={saving}
            onEvidenceTypeChange={setEvidenceType}
            onSectionChange={setSection}
            onActionIdChange={setActionId}
            onDescriptionChange={setDescription}
          />
          <FormActions align="end">
            <button type="button" className={PAC_GHOST_BTN} disabled={saving} onClick={onClose}>
              Cancelar
            </button>
            <button
              type="button"
              className="pac-primary-btn"
              disabled={saving}
              onClick={() => void handleSave()}
            >
              {saving ? "Salvando…" : "Salvar"}
            </button>
          </FormActions>
        </div>
      ) : null}
    </Modal>
  );
}
