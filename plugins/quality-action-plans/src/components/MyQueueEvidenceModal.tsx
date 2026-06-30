import { Upload } from "lucide-react";
import { useRef, useState } from "react";

import { uploadPlanEvidence } from "../api/actionPlansApi";
import { EVIDENCE_TYPE_OPTIONS } from "../constants/evidence";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { MyQueueItem } from "../types/myQueue";
import { StateAlert } from "./StateAlert";
import { FormActions } from "./ui/FormActions";
import { Modal } from "./ui/Modal";
import { SelectField } from "./ui/SelectField";
import { TextField } from "./ui/TextField";

type Props = {
  item: MyQueueItem | null;
  open: boolean;
  onClose: () => void;
  onUploaded: () => void | Promise<void>;
};

export function MyQueueEvidenceModal({ item, open, onClose, onUploaded }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [evidenceType, setEvidenceType] = useState("image");
  const [description, setDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    if (!item) {
      return;
    }
    setUploading(true);
    setError(null);
    try {
      await uploadPlanEvidence(item.plan_id, file, {
        evidenceType,
        section: "corrective",
        actionId: item.action_id,
        description: description.trim() || undefined,
        knowledgeVisible: true,
      });
      setDescription("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await onUploaded();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao anexar evidência.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <Modal
      open={open}
      title="Anexar evidência à ação"
      className="pac-modal--my-queue-evidence"
      onClose={() => {
        if (!uploading) {
          onClose();
        }
      }}
    >
      {item ? (
        <div className="pac-my-queue-evidence-modal">
          <p className="pac-my-queue-evidence-modal__context">
            <strong>{item.plan_code ?? item.plan_id}</strong>
            <span className="pac-my-queue-evidence-modal__context-text">{item.description}</span>
          </p>
          {error ? <StateAlert variant="error">{error}</StateAlert> : null}
          <div className="pac-my-queue-evidence-modal__fields">
            <SelectField
              id="pac-queue-evidence-type"
              label="Tipo do arquivo"
              hint={PAC_HELP_TOOLTIPS.form.actionEvidence}
              options={EVIDENCE_TYPE_OPTIONS.map((option) => ({
                value: option.value,
                label: option.label,
              }))}
              value={evidenceType}
              onChange={setEvidenceType}
              searchable={false}
            />
            <TextField
              id="pac-queue-evidence-desc"
              label="Descrição (opcional)"
              hint={PAC_HELP_TOOLTIPS.form.actionEvidence}
              value={description}
              onChange={setDescription}
              fullWidth
              placeholder="Ex.: foto do lote bloqueado, e-mail do cliente…"
            />
          </div>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            disabled={uploading}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                void handleUpload(file);
              }
            }}
          />
          <FormActions align="end">
            <button
              type="button"
              className="pac-ghost-btn"
              disabled={uploading}
              onClick={onClose}
            >
              Fechar
            </button>
            <button
              type="button"
              className="pac-primary-btn"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={16} aria-hidden="true" />
              {uploading ? "Enviando…" : "Selecionar arquivo"}
            </button>
          </FormActions>
        </div>
      ) : null}
    </Modal>
  );
}
