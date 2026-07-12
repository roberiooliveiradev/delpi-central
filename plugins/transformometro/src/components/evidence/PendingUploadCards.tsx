import { useEffect, useState } from "react";
import { ChevronDown, FileText, X } from "lucide-react";

import {
  FilePreviewModal,
  NativeTextControl,
  canPreviewFile,
  resolveFilePreviewKind,
} from "@delpi/plugin-ui/index";

import { formatEvidenceFileSize } from "../../data/api/transformometroEvidenceApi";

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

function canPreviewPendingFile(file: File): boolean {
  return canPreviewFile({ mimeType: file.type, fileName: file.name });
}

function isImageFile(file: File): boolean {
  return resolveFilePreviewKind({ mimeType: file.type, fileName: file.name }) === "image";
}

function isPdfFile(file: File): boolean {
  return resolveFilePreviewKind({ mimeType: file.type, fileName: file.name }) === "pdf";
}

function useFileObjectUrl(file: File): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!canPreviewPendingFile(file)) {
      setUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  return url;
}

function isSpreadsheetFile(file: File): boolean {
  return resolveFilePreviewKind({ mimeType: file.type, fileName: file.name }) === "spreadsheet";
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

  if (isSpreadsheetFile(file)) {
    return (
      <div className="tm-evidence__file-icon tm-evidence__file-icon--spreadsheet" aria-hidden="true">
        <FileText size={24} />
        <span>XLSX</span>
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
  const previewable = canPreviewPendingFile(item.file);

  return (
    <article className="tm-evidence-pending-card">
      <div className="tm-evidence-pending-card__thumb">
        <button
          type="button"
          className="tm-evidence-pending-card__remove"
          disabled={disabled}
          onClick={(event) => {
            event.stopPropagation();
            onRemove(item.id);
          }}
          aria-label={`Remover ${item.file.name}`}
        >
          <X size={14} aria-hidden="true" />
        </button>

        {previewable ? (
          <button
            type="button"
            className="tm-evidence__thumb-btn tm-evidence-pending-card__thumb-btn"
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
      </div>

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
        <NativeTextControl
          type="text"
          placeholder="Ex.: POP vigente, instrução de trabalho…"
          value={item.descricao}
          disabled={disabled}
          onChange={(value) => onUpdateDescription(item.id, value)}
        />
      </details>

      <FilePreviewModal
        open={previewOpen}
        title={item.file.name}
        onClose={() => setPreviewOpen(false)}
        source={item.file}
        mimeType={item.file.type}
        fileName={item.file.name}
        enabled={previewable}
        metaItems={[formatEvidenceFileSize(item.file.size), item.file.type || "Tipo não informado"]}
      />
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
