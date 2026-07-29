import { ChevronDown, Eye, FileText, X } from "lucide-react";
import { useEffect, useState } from "react";

import type { KaizenEvidenceStage } from "../../types/kaizen";
import { EVIDENCE_STAGE_LABELS, EVIDENCE_STAGE_OPTIONS } from "../../constants/evidenceStages";
import { SelectField, TextAreaField } from "../ui";
import { formatEvidenceFileSize, isImageFile } from "./kaizenEvidenceUtils";
import { canPreviewLocalFile } from "./kaizenEvidencePreview";

export type KaizenPendingUpload = {
  id: string;
  file: File;
  stage: KaizenEvidenceStage;
  description: string;
};

type Props = {
  items: KaizenPendingUpload[];
  disabled?: boolean;
  onChange: (id: string, patch: Partial<KaizenPendingUpload>) => void;
  onRemove: (id: string) => void;
  onPreview?: (file: File) => void;
};

function PendingThumb({ file }: { file: File }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!isImageFile(file)) return undefined;
    const url = URL.createObjectURL(file);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  if (objectUrl) {
    return <img className="kz-pending__thumb" src={objectUrl} alt={file.name} />;
  }
  return (
    <div className="kz-pending__thumb kz-pending__thumb--file" aria-hidden="true">
      <FileText size={20} />
    </div>
  );
}

function PendingItem({
  item,
  disabled,
  onChange,
  onRemove,
  onPreview,
}: {
  item: KaizenPendingUpload;
  disabled: boolean;
  onChange: (id: string, patch: Partial<KaizenPendingUpload>) => void;
  onRemove: (id: string) => void;
  onPreview?: (file: File) => void;
}) {
  const [open, setOpen] = useState(false);
  const previewable = Boolean(onPreview) && canPreviewLocalFile(item.file);
  const detailsId = `kz-pending-details-${item.id}`;

  return (
    <li className={`kz-pending${open ? " kz-pending--open" : ""}`}>
      <div className="kz-pending__top">
        {previewable ? (
          <button
            type="button"
            className="kz-pending__thumb-btn"
            onClick={() => onPreview?.(item.file)}
            aria-label={`Pré-visualizar ${item.file.name}`}
          >
            <PendingThumb file={item.file} />
          </button>
        ) : (
          <PendingThumb file={item.file} />
        )}

        <div className="kz-pending__body">
          <div className="kz-pending__head">
            <span className="kz-pending__name" title={item.file.name}>
              {item.file.name}
            </span>
            <span className="kz-pending__size">{formatEvidenceFileSize(item.file.size)}</span>
          </div>
          <span className="kz-pending__badge">{EVIDENCE_STAGE_LABELS[item.stage]}</span>
        </div>

        <div className="kz-pending__actions">
          <button
            type="button"
            className={`kz-pending__action${open ? " kz-pending__action--active" : ""}`}
            aria-expanded={open}
            aria-controls={detailsId}
            aria-label={open ? "Ocultar detalhes" : "Editar etapa e descrição"}
            onClick={() => setOpen((current) => !current)}
          >
            <ChevronDown size={14} aria-hidden="true" />
          </button>
          {previewable ? (
            <button
              type="button"
              className="kz-pending__action"
              disabled={disabled}
              aria-label={`Pré-visualizar ${item.file.name}`}
              onClick={() => onPreview?.(item.file)}
            >
              <Eye size={14} aria-hidden="true" />
            </button>
          ) : null}
          <button
            type="button"
            className="kz-pending__remove"
            disabled={disabled}
            aria-label={`Remover ${item.file.name} da fila`}
            onClick={() => onRemove(item.id)}
          >
            <X size={14} aria-hidden="true" />
          </button>
        </div>
      </div>

      {open ? (
        <div className="kz-pending__details" id={detailsId}>
          <SelectField
            id={`${item.id}-stage`}
            label="Etapa"
            value={item.stage}
            onChange={(value) => onChange(item.id, { stage: value as KaizenEvidenceStage })}
            options={EVIDENCE_STAGE_OPTIONS}
            className="kz-pending__field kz-pending__field--stage"
          />
          <TextAreaField
            id={`${item.id}-desc`}
            label="Descrição"
            rows={3}
            span={false}
            value={item.description}
            onChange={(value) => onChange(item.id, { description: value })}
            className="kz-pending__field kz-pending__field--desc"
          />
        </div>
      ) : null}
    </li>
  );
}

export function KaizenEvidencePendingList({
  items,
  disabled = false,
  onChange,
  onRemove,
  onPreview,
}: Props) {
  return (
    <ul className="kz-pending-list">
      {items.map((item) => (
        <PendingItem
          key={item.id}
          item={item}
          disabled={disabled}
          onChange={onChange}
          onRemove={onRemove}
          onPreview={onPreview}
        />
      ))}
    </ul>
  );
}
