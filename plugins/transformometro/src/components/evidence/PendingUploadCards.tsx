import { useEffect, useState } from "react";
import { ChevronDown, FileText, X } from "lucide-react";

import { formatEvidenceFileSize } from "../../data/api/transformometroEvidenceApi";
import { Modal } from "../ui/Modal";

export type PendingUploadItem = {
  id: string;
  file: File;
  descricao: string;
};

type Props = {
  items: PendingUploadItem[];
  disabled?: boolean;
  onUpdateDescription: (id: string, descricao: string) => void;
  onRemove: (id: string) => void;
};

function isImageFile(file: File): boolean {
  return file.type.startsWith("image/");
}

function isPdfFile(file: File): boolean {
  return file.type === "application/pdf";
}

function canPreviewFile(file: File): boolean {
  return isImageFile(file) || isPdfFile(file);
}

function useFileObjectUrl(file: File): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!canPreviewFile(file)) {
      setUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  return url;
}

function PendingFilePreview({
  file,
  previewUrl,
}: {
  file: File;
  previewUrl: string | null;
}) {
  if (isImageFile(file) && previewUrl) {
    return (
      <img
        className="tm-evidence__img"
        src={previewUrl}
        alt={file.name}
        loading="lazy"
      />
    );
  }

  if (isPdfFile(file)) {
    return (
      <div className="tm-evidence__file-icon tm-evidence__file-icon--pdf" aria-hidden="true">
        <FileText size={24} />
        <span>PDF</span>
      </div>
    );
  }

  return (
    <div className="tm-evidence__file-icon" aria-hidden="true">
      <FileText size={24} />
    </div>
  );
}

function PendingUploadCard({
  item,
  disabled,
  onUpdateDescription,
  onRemove,
}: {
  item: PendingUploadItem;
  disabled: boolean;
  onUpdateDescription: (id: string, descricao: string) => void;
  onRemove: (id: string) => void;
}) {
  const previewUrl = useFileObjectUrl(item.file);
  const [previewOpen, setPreviewOpen] = useState(false);
  const previewable = canPreviewFile(item.file);

  return (
    <article className="tm-evidence-pending-card">
      <button
        type="button"
        className="tm-evidence-pending-card__remove"
        disabled={disabled}
        onClick={() => onRemove(item.id)}
        aria-label={`Remover ${item.file.name}`}
      >
        <X size={14} aria-hidden="true" />
      </button>

      {previewable ? (
        <button
          type="button"
          className="tm-evidence__thumb-btn"
          disabled={disabled}
          onClick={() => setPreviewOpen(true)}
          aria-label={`Pré-visualizar ${item.file.name}`}
        >
          <PendingFilePreview file={item.file} previewUrl={previewUrl} />
        </button>
      ) : (
        <div className="tm-evidence-pending-card__static-thumb">
          <PendingFilePreview file={item.file} previewUrl={previewUrl} />
        </div>
      )}

      <div className="tm-evidence-pending-card__meta">
        <span className="tm-evidence-pending-card__name" title={item.file.name}>
          {item.file.name}
        </span>
        <span className="tm-evidence-pending-card__size">
          {formatEvidenceFileSize(item.file.size)}
        </span>
      </div>

      <details className="tm-evidence-pending-card__desc">
        <summary>
          <ChevronDown size={14} aria-hidden="true" className="tm-evidence-pending-card__chevron" />
          Descrição (opcional)
        </summary>
        <input
          type="text"
          placeholder="Ex.: POP vigente, instrução de trabalho…"
          value={item.descricao}
          disabled={disabled}
          onChange={(event) => onUpdateDescription(item.id, event.target.value)}
        />
      </details>

      <Modal
        open={previewOpen}
        title={item.file.name}
        onClose={() => setPreviewOpen(false)}
        className="ds-modal--evidence-preview"
      >
        <div className="tm-evidence-preview-modal">
          {isImageFile(item.file) && previewUrl ? (
            <img
              className="tm-evidence-preview-modal__img"
              src={previewUrl}
              alt={item.file.name}
            />
          ) : isPdfFile(item.file) && previewUrl ? (
            <iframe
              className="tm-evidence-preview-modal__pdf"
              src={previewUrl}
              title={item.file.name}
            />
          ) : (
            <p className="ds-hint">Pré-visualização indisponível para este tipo de arquivo.</p>
          )}
        </div>
      </Modal>
    </article>
  );
}

export function PendingUploadCards({
  items,
  disabled = false,
  onUpdateDescription,
  onRemove,
}: Props) {
  if (!items.length) return null;

  return (
    <div className="tm-evidence-pending-grid" role="list">
      {items.map((item) => (
        <PendingUploadCard
          key={item.id}
          item={item}
          disabled={disabled}
          onUpdateDescription={onUpdateDescription}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
}
