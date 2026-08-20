import { useEffect, useRef, useState } from "react";
import { ImagePlus, Save } from "lucide-react";

import type { KaizenEvidence, KaizenEvidenceStage } from "../../types/kaizen";
import { EVIDENCE_STAGE_OPTIONS } from "../../constants/evidenceStages";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  FormActions,
  FormGrid,
  SelectField,
  TextAreaField,
  TextField,
  TitleWithHelp,
} from "../ui";
import { KZ_GHOST_BTN } from "../ui/ghostChrome";
import { formatEvidenceFileSize, isImageFile } from "./kaizenEvidenceUtils";

type Props = {
  evidence: KaizenEvidence;
  saving?: boolean;
  onCancel: () => void;
  onSave: (payload: {
    stage: KaizenEvidenceStage;
    description: string;
    externalUrl?: string;
    file?: File;
  }) => void;
};

export function KaizenEvidenceEditForm({
  evidence,
  saving = false,
  onCancel,
  onSave,
}: Props) {
  const [stage, setStage] = useState<KaizenEvidenceStage>(evidence.stage);
  const [description, setDescription] = useState(evidence.description ?? "");
  const [externalUrl, setExternalUrl] = useState(evidence.external_url ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    setStage(evidence.stage);
    setDescription(evidence.description ?? "");
    setExternalUrl(evidence.external_url ?? "");
    setFile(null);
  }, [evidence]);

  useEffect(() => {
    rootRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [evidence.id]);

  useEffect(() => {
    if (!file || !isImageFile(file)) {
      setPreviewUrl(null);
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const isLink = evidence.type === "link";
  const canSave = !saving && (isLink ? externalUrl.trim().length > 0 : true);

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
    <section
      ref={rootRef}
      className="kz-evidence-edit"
      aria-labelledby="kz-evidence-edit-title"
    >
      <header className="kz-evidence-edit__head">
        <div className="kz-evidence-edit__title" id="kz-evidence-edit-title">
          <TitleWithHelp
            title="Editar evidência"
            hint={KAIZEN_HELP_TOOLTIPS.evidence.edit}
          />
        </div>
        <p className="kz-evidence-edit__hint">{KAIZEN_HELP_TOOLTIPS.evidence.edit}</p>
      </header>

      <FormGrid>
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
          <div className="kz-evidence-edit__file kz-span-2">
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
                setFile(event.target.files?.[0] ?? null);
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
      </FormGrid>

      <FormActions align="end">
        <button
          type="button"
          className={KZ_GHOST_BTN}
          disabled={saving}
          onClick={onCancel}
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
      </FormActions>
    </section>
  );
}
