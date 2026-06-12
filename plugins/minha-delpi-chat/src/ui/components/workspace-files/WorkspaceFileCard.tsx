import { Download, Eye, FileText, Image as ImageIcon, Trash2, X } from "lucide-react";
import type { ReactNode } from "react";

import "./workspaceFileIngest.css";

export type WorkspaceFileCardVariant = "card" | "chip" | "row";

export type WorkspaceFileCardProps = {
  variant?: WorkspaceFileCardVariant;
  filename: string;
  sizeLabel?: string;
  statusLabel?: string;
  thumb?: ReactNode;
  previewKind?: "image" | "file";
  editable?: boolean;
  secondaryLabel?: string;
  onPreview?: () => void;
  onDownload?: () => void;
  onRemove?: () => void;
};

export function WorkspaceFileCard({
  variant = "card",
  filename,
  sizeLabel,
  statusLabel,
  thumb,
  previewKind = "file",
  editable = false,
  secondaryLabel,
  onPreview,
  onDownload,
  onRemove,
}: WorkspaceFileCardProps) {
  const actionButtons = (
    <>
      {onPreview ? (
        <button
          type="button"
          className="mdc-workspace-file-card__action"
          onClick={onPreview}
          aria-label={`Abrir pré-visualização de ${filename}`}
          title="Pré-visualizar"
        >
          <Eye size={15} aria-hidden="true" />
        </button>
      ) : null}

      {onDownload ? (
        <button
          type="button"
          className="mdc-workspace-file-card__action"
          onClick={onDownload}
          aria-label={`Baixar ${filename}`}
          title="Baixar arquivo"
        >
          <Download size={15} aria-hidden="true" />
        </button>
      ) : null}

      {editable && onRemove ? (
        <button
          type="button"
          className="mdc-workspace-file-card__action mdc-workspace-file-card__action--danger"
          onClick={onRemove}
          aria-label={`Remover ${filename}`}
          title="Remover anexo"
        >
          <Trash2 size={15} aria-hidden="true" />
        </button>
      ) : null}
    </>
  );

  if (variant === "chip") {
    return (
      <span className="mdc-workspace-file-card mdc-workspace-file-card--chip">
        {previewKind === "image" ? (
          <ImageIcon size={14} aria-hidden="true" />
        ) : (
          <FileText size={14} aria-hidden="true" />
        )}
        <strong title={filename}>{filename}</strong>
        {sizeLabel ? <small>{sizeLabel}</small> : null}
        {statusLabel ? (
          <small className="mdc-workspace-file-card__status">{statusLabel}</small>
        ) : null}
        {onPreview ? (
          <button
            type="button"
            className="mdc-workspace-file-card__chip-action"
            onClick={onPreview}
            aria-label={`Pré-visualizar ${filename}`}
            title="Pré-visualizar"
          >
            <Eye size={13} aria-hidden="true" />
          </button>
        ) : null}

        {editable && onRemove ? (
          <button
            type="button"
            className="mdc-workspace-file-card__chip-action mdc-workspace-file-card__remove"
            onClick={onRemove}
            aria-label={`Remover ${filename}`}
          >
            <X size={13} aria-hidden="true" />
          </button>
        ) : null}
      </span>
    );
  }

  if (variant === "row") {
    return (
      <article className="mdc-workspace-file-card mdc-workspace-file-card--row">
        <div className="mdc-workspace-file-card__row-body">
          <span className="mdc-workspace-file-card__row-icon" aria-hidden="true">
            {previewKind === "image" ? <ImageIcon size={18} /> : <FileText size={18} />}
          </span>

          <div className="mdc-workspace-file-card__meta">
            <strong title={filename}>{filename}</strong>
            <div className="mdc-workspace-file-card__details">
              {sizeLabel ? <span>{sizeLabel}</span> : null}
              {statusLabel ? <span>{statusLabel}</span> : null}
              {secondaryLabel ? <span>{secondaryLabel}</span> : null}
            </div>
          </div>
        </div>

        <div className="mdc-workspace-file-card__actions">{actionButtons}</div>
      </article>
    );
  }

  const meta = (
    <>
      <div className="mdc-workspace-file-card__thumb" aria-hidden="true">
        {thumb ??
          (previewKind === "image" ? <ImageIcon size={20} /> : <FileText size={20} />)}
      </div>

      <div className="mdc-workspace-file-card__meta">
        <strong title={filename}>{filename}</strong>
        <div className="mdc-workspace-file-card__details">
          {sizeLabel ? <span>{sizeLabel}</span> : null}
          {statusLabel ? <span>{statusLabel}</span> : null}
          {secondaryLabel ? <span>{secondaryLabel}</span> : null}
        </div>
      </div>
    </>
  );

  return (
    <article className="mdc-workspace-file-card mdc-workspace-file-card--card">
      {onPreview ? (
        <button
          type="button"
          className="mdc-workspace-file-card__preview-hit"
          onClick={onPreview}
          aria-label={`Pré-visualizar ${filename}`}
        >
          {meta}
        </button>
      ) : (
        <div className="mdc-workspace-file-card__preview-hit mdc-workspace-file-card__preview-hit--static">
          {meta}
        </div>
      )}

      <div className="mdc-workspace-file-card__actions">{actionButtons}</div>
    </article>
  );
}
