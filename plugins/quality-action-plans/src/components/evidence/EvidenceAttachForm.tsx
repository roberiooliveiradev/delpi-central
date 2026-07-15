import { useState } from "react";
import { Upload } from "lucide-react";

import { uploadPlanEvidence } from "../../api/actionPlansApi";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { PlanAction } from "../../types/actionPlan";
import { StateAlert } from "../StateAlert";
import { FormActions } from "../ui/FormActions";
import {
  createPendingUploadId,
  inferEvidenceTypeFromFile,
} from "./evidenceAttachmentUtils";
import { EvidenceFileDropzone } from "./EvidenceFileDropzone";
import { EvidencePendingUploadList } from "./EvidencePendingUploadList";
import type { EvidencePendingUpload } from "./EvidencePendingUploadItem";
import { PAC_GHOST_BTN } from "../ui/ghostChrome";

type Props = {
  planId: string;
  actions?: PlanAction[];
  defaultSection?: string;
  defaultActionId?: string;
  lockActionId?: boolean;
  disabled?: boolean;
  onUploaded: () => void | Promise<void>;
  onClose?: () => void;
  showFooter?: boolean;
  submitLabel?: string;
};

export function EvidenceAttachForm({
  planId,
  actions = [],
  defaultSection = "general",
  defaultActionId = "",
  lockActionId = false,
  disabled = false,
  onUploaded,
  onClose,
  showFooter = false,
  submitLabel,
}: Props) {
  const [pending, setPending] = useState<EvidencePendingUpload[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addFiles(files: File[]) {
    if (!files.length || disabled || uploading) return;
    setError(null);
    setPending((current) => [
      ...current,
      ...files.map((file) => ({
        id: createPendingUploadId(),
        file,
        evidenceType: inferEvidenceTypeFromFile(file),
        section: defaultSection,
        actionId: defaultActionId,
        description: "",
      })),
    ]);
  }

  function updatePending(id: string, patch: Partial<EvidencePendingUpload>) {
    setPending((current) =>
      current.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    );
  }

  function removePending(id: string) {
    setPending((current) => current.filter((item) => item.id !== id));
  }

  async function handleSubmit() {
    if (!pending.length || uploading) return;
    setUploading(true);
    setError(null);
    try {
      for (const item of pending) {
        await uploadPlanEvidence(planId, item.file, {
          evidenceType: item.evidenceType,
          section: item.section,
          actionId: item.actionId || undefined,
          description: item.description.trim() || undefined,
          knowledgeVisible: true,
        });
      }
      setPending([]);
      await onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar anexos.");
    } finally {
      setUploading(false);
    }
  }

  const uploadButtonLabel =
    submitLabel
    ?? (pending.length > 1
      ? `Enviar ${pending.length} anexos`
      : pending.length === 1
        ? "Enviar anexo"
        : "Enviar anexos");

  return (
    <div className="pac-evidence-attach-form">
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <EvidenceFileDropzone
        disabled={disabled || uploading}
        onFilesSelected={addFiles}
      />

      {pending.length ? (
        <EvidencePendingUploadList
          items={pending}
          actions={actions}
          lockActionId={lockActionId}
          disabled={disabled || uploading}
          onChange={updatePending}
          onRemove={removePending}
        />
      ) : (
        <p className="pac-muted pac-evidence-attach-form__empty">
          Nenhum arquivo na fila. Use a área acima para adicionar anexos.
        </p>
      )}

      {showFooter ? (
        <FormActions align="end">
          {onClose ? (
            <button
              type="button"
              className={PAC_GHOST_BTN}
              disabled={uploading}
              onClick={onClose}
            >
              Fechar
            </button>
          ) : null}
          <button
            type="button"
            className="pac-primary-btn"
            disabled={disabled || uploading || pending.length === 0}
            title={PAC_HELP_TOOLTIPS.evidence.upload}
            onClick={() => void handleSubmit()}
          >
            <Upload size={16} aria-hidden="true" />
            {uploading ? "Enviando…" : uploadButtonLabel}
          </button>
        </FormActions>
      ) : (
        <div className="pac-evidence-attach-form__submit">
          <button
            type="button"
            className="pac-primary-btn"
            disabled={disabled || uploading || pending.length === 0}
            title={PAC_HELP_TOOLTIPS.evidence.upload}
            onClick={() => void handleSubmit()}
          >
            <Upload size={16} aria-hidden="true" />
            {uploading ? "Enviando…" : uploadButtonLabel}
          </button>
        </div>
      )}
    </div>
  );
}
