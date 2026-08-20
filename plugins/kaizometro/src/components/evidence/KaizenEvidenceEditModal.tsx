import { useEffect, useRef, useState } from "react";
import { ImagePlus, Save } from "lucide-react";

import type { KaizenEvidence, KaizenEvidenceStage } from "../../types/kaizen";
import { EVIDENCE_STAGE_OPTIONS } from "../../constants/evidenceStages";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { Modal, SelectField, TextAreaField, TextField } from "../ui";
import { KZ_GHOST_BTN } from "../ui/ghostChrome";
import { formatEvidenceFileSize, isImageFile } from "./kaizenEvidenceUtils";

type Props = {
  open: boolean;
  evidence: KaizenEvidence | null;
  saving?: boolean;
  onClose: () => void;
  onSave: (payload: {
    stage: KaizenEvidenceStage;
    description: string;
    externalUrl?: string;
    file?: File;
  }) => void;
};

export function KaizenEvidenceEditModal({
  open,
  evidence,
  saving = false,
  onClose,
  onSave,
}: Props) {
  const [stage, setStage] = useState<KaizenEvidenceStage>("geral");
  const [description, setDescription] = useState("");
  const [externalUrl, setExternalUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open || !evidence) return;
    setStage(evidence.stage);
    setDescription(evidence.description ?? "");
    setExternalUrl(evidence.external_url ?? "");
    setFile(null);
  }, [open, evidence]);

  useEffect(() => {
    if (!file || !isImageFile(file)) {
      setPreviewUrl(null);
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  if (!evidence) return null;

  const isLink = evidence.type === "link";
  const canSave =
    !saving &&
    (isLink ? externalUrl.trim().length > 0 : true);

  function handleSubmit() {
    if (!canSave) return;
    onSave({
      stage,
      description: description.trim(),
      externalUrl: isLink ? externalUrl.trim() : undefined,
      file: file ?? undefined,
    });
  }

  return (
    <Modal open={open} title="Editar evidência" onClose={saving ? () => undefined : onClose}>
      <div className="kz-evidence-edit">
        <p className="kz-evidence-edit__hint">{KAIZEN_HELP_TOOLTIPS.evidence.edit}</p>

        <SelectField
          id="kz-ev-edit-stage"
          label="Etapa"
          hint={KAIZEN_HELP_TOOLTIPS.evidence.stage}
          value={stage}
          onChange={(value) => setStage(value as KaizenEvidenceStage)}
          options={EVIDENCE_STAGE_OPTIONS}
        />

        <TextAreaField
          id="kz-ev-edit-desc"
          label="Descrição"
          hint={KAIZEN_HELP_TOOLTIPS.evidence.description}
          rows={6}
          span
          value={description}
          onChange={setDescription}
        />

        {isLink ? (
          <TextField
            id="kz-ev-edit-url"
            label="URL"
            hint={KAIZEN_HELP_TOOLTIPS.evidence.link}
            placeholder="https://…"
            value={externalUrl}
            onChange={setExternalUrl}
          />
        ) : (
          <div className="kz-evidence-edit__file">
            <span className="kz-evidence-edit__file-label">Arquivo / foto</span>
            <p className="kz-evidence-edit__file-current">
              Atual: {evidence.file_name || "arquivo"}
              {evidence.size_bytes != null
                ? ` · ${formatEvidenceFileSize(evidence.size_bytes)}`
                : ""}
            </p>
            {previewUrl ? (
              <img
                className="kz-evidence-edit__preview"
                src={previewUrl}
                alt="Prévia do novo arquivo"
              />
            ) : null}
            <input
              ref={fileInputRef}
              type="file"
              className="kz-evidence-edit__file-input"
              accept="image/*,.pdf,.xlsx,.xls,.csv,.doc,.docx,.txt"
              onChange={(event) => {
                const next = event.target.files?.[0] ?? null;
                setFile(next);
              }}
            />
            <button
              type="button"
              className={KZ_GHOST_BTN}
              disabled={saving}
              onClick={() => fileInputRef.current?.click()}
            >
              <ImagePlus size={14} aria-hidden="true" />
              {file ? `Novo: ${file.name}` : "Trocar foto ou arquivo"}
            </button>
          </div>
        )}

        <div className="kz-evidence-edit__actions">
          <button
            type="button"
            className={KZ_GHOST_BTN}
            disabled={saving}
            onClick={onClose}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="kz-primary-btn"
            disabled={!canSave}
            onClick={handleSubmit}
          >
            <Save size={14} aria-hidden="true" />
            {saving ? "Salvando…" : "Salvar alterações"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
