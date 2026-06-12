import { Download, Eye, FileText, Image as ImageIcon, Trash2, X } from "lucide-react";
import type { ReactNode } from "react";

import type { WorkspaceFileStatusTone } from "../../../content/workspaceFileIngestContent";

import "./workspaceFileIngest.css";

export type WorkspaceFileCardVariant = "card" | "chip" | "row";

export type WorkspaceFileCardProps = {
  variant?: WorkspaceFileCardVariant;
  filename: string;
  sizeLabel?: string;
  statusLabel?: string;
  statusTone?: WorkspaceFileStatusTone;
  thumb?: ReactNode;
  previewKind?: "image" | "file";
  editable?: boolean;
  secondaryLabel?: string;
  onPreview?: () => void;
  onDownload?: () => void;
  onRemove?: () => void;
};

type DetailItem = {
  key: string;
  text: string;
  tone?: WorkspaceFileStatusTone;
};

function detailClassName(tone?: WorkspaceFileStatusTone): string {
  return tone && tone !== "default"
    ? `mdc-workspace-file-card__detail mdc-workspace-file-card__detail--${tone}`
    : "mdc-workspace-file-card__detail";
}

function FileCardDetails({
  sizeLabel,
  statusLabel,
  statusTone = "default",
  secondaryLabel,
}: Pick<
  WorkspaceFileCardProps,
  "sizeLabel" | "statusLabel" | "statusTone" | "secondaryLabel"
>) {
  const items: DetailItem[] = [];

  if (sizeLabel) {
    items.push({ key: "size", text: sizeLabel });
  }

  if (statusLabel) {
    items.push({ key: "status", text: statusLabel, tone: statusTone });
  }

  if (secondaryLabel) {
    items.push({ key: "secondary", text: secondaryLabel });
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="mdc-workspace-file-card__details">
      {items.map((item) => (
        <span key={item.key} className={detailClassName(item.tone)}>
          {item.text}
        </span>
      ))}
    </div>
  );
}

function FileCardIcon({
  previewKind,
  thumb,
  compact = false,
}: {
  previewKind: "image" | "file";
  thumb?: ReactNode;
  compact?: boolean;
}) {
  const iconSize = compact ? 16 : 18;

  return (
    <span className="mdc-workspace-file-card__icon" aria-hidden="true">
      {thumb ?? (previewKind === "image" ? <ImageIcon size={iconSize} /> : <FileText size={iconSize} />)}
    </span>
  );
}

export function WorkspaceFileCard({
  variant = "card",
  filename,
  sizeLabel,
  statusLabel,
  statusTone = "default",
  thumb,
  previewKind = "file",
  editable = false,
  onPreview,
  onDownload,
  onRemove,
  secondaryLabel,
}: WorkspaceFileCardProps) {
  const actionButtons = (
    <div className="mdc-workspace-file-card__actions">
      {onPreview ? (
        <button
          type="button"
          className="mdc-workspace-file-card__action"
          onClick={onPreview}
          aria-label={`Abrir pré-visualização de ${filename}`}
          title="Pré-visualizar"
        >
          <Eye size={14} aria-hidden="true" />
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
          <Download size={14} aria-hidden="true" />
        </button>
      ) : null}

      {editable && onRemove ? (
        <button
          type="button"
          className="mdc-workspace-file-card__action mdc-workspace-file-card__action--danger"
          onClick={onRemove}
          aria-label={`Remover ${filename}`}
          title="Remover arquivo"
        >
          <Trash2 size={14} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );

  const meta = (
    <div className="mdc-workspace-file-card__meta">
      <strong title={filename}>{filename}</strong>
      <FileCardDetails
        sizeLabel={sizeLabel}
        statusLabel={statusLabel}
        statusTone={statusTone}
        secondaryLabel={secondaryLabel}
      />
    </div>
  );

  if (variant === "chip") {
    return (
      <span className="mdc-workspace-file-card mdc-workspace-file-card--chip">
        <FileCardIcon previewKind={previewKind} compact />
        <strong title={filename}>{filename}</strong>
        {sizeLabel ? <small className="mdc-workspace-file-card__chip-meta">{sizeLabel}</small> : null}
        {statusLabel ? (
          <small className={detailClassName(statusTone)}>{statusLabel}</small>
        ) : null}
        <span className="mdc-workspace-file-card__chip-actions">
          {onPreview ? (
            <button
              type="button"
              className="mdc-workspace-file-card__chip-action"
              onClick={onPreview}
              aria-label={`Pré-visualizar ${filename}`}
              title="Pré-visualizar"
            >
              <Eye size={12} aria-hidden="true" />
            </button>
          ) : null}

          {editable && onRemove ? (
            <button
              type="button"
              className="mdc-workspace-file-card__chip-action"
              onClick={onRemove}
              aria-label={`Remover ${filename}`}
            >
              <X size={12} aria-hidden="true" />
            </button>
          ) : null}
        </span>
      </span>
    );
  }

  const body = (
    <>
      <FileCardIcon previewKind={previewKind} thumb={thumb} compact={variant === "row"} />
      {meta}
    </>
  );

  if (variant === "row") {
    return (
      <article className="mdc-workspace-file-card mdc-workspace-file-card--row">
        {onPreview ? (
          <button
            type="button"
            className="mdc-workspace-file-card__body mdc-workspace-file-card__body--interactive"
            onClick={onPreview}
            aria-label={`Pré-visualizar ${filename}`}
          >
            {body}
          </button>
        ) : (
          <div className="mdc-workspace-file-card__body">{body}</div>
        )}
        {actionButtons}
      </article>
    );
  }

  return (
    <article className="mdc-workspace-file-card mdc-workspace-file-card--card">
      <div className="mdc-workspace-file-card__surface">
        {onPreview ? (
          <button
            type="button"
            className="mdc-workspace-file-card__body mdc-workspace-file-card__body--interactive"
            onClick={onPreview}
            aria-label={`Pré-visualizar ${filename}`}
          >
            {body}
          </button>
        ) : (
          <div className="mdc-workspace-file-card__body">{body}</div>
        )}
        {actionButtons}
      </div>
    </article>
  );
}
