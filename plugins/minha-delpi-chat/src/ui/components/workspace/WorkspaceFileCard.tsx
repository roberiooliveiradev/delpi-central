import {
  Download,
  Eye,
  FileText,
  Image as ImageIcon,
  Loader2,
  Trash2,
  X,
} from "lucide-react";
import type { ReactNode } from "react";

import {
  ingestProgressPercentLabel,
  resolveIngestProgressPercent,
} from "../../../content/ingestProgress";
import type {
  WorkspaceFileIconTone,
  WorkspaceFileIngestProgress,
  WorkspaceFileStatusTone,
} from "../../../content/workspaceFileIngestContent";

import "./workspaceFileIngest.css";

export type WorkspaceFileCardVariant = "card" | "chip" | "row";

export type { WorkspaceFileIngestProgress } from "../../../content/workspaceFileIngestContent";

export type WorkspaceFileCardProps = {
  variant?: WorkspaceFileCardVariant;
  filename: string;
  kindLabel?: string;
  /** Segunda linha em card/chip (ex.: tamanho do arquivo). */
  subtitleLabel?: string;
  sizeLabel?: string;
  statusLabel?: string;
  statusTone?: WorkspaceFileStatusTone;
  iconTone?: WorkspaceFileIconTone;
  thumb?: ReactNode;
  previewKind?: "image" | "file";
  editable?: boolean;
  secondaryLabel?: string;
  showInlineActions?: boolean;
  dismissRemove?: boolean;
  ingestProgress?: WorkspaceFileIngestProgress;
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
  iconTone = "brand",
  compact = false,
}: {
  previewKind: "image" | "file";
  thumb?: ReactNode;
  iconTone?: WorkspaceFileIconTone;
  compact?: boolean;
}) {
  const iconSize = compact ? 16 : 18;

  return (
    <span
      className={`mdc-workspace-file-card__icon mdc-workspace-file-card__icon--${iconTone}`}
      aria-hidden="true"
    >
      {iconTone === "pending" ? (
        <Loader2 size={iconSize} className="mdc-workspace-file-card__icon-spinner" />
      ) : thumb ? (
        thumb
      ) : previewKind === "image" ? (
        <ImageIcon size={iconSize} />
      ) : (
        <FileText size={iconSize} />
      )}
    </span>
  );
}

function FileCardIngestProgress({
  percent,
  label,
}: {
  percent?: number | null;
  label?: string;
}) {
  const resolvedPercent = resolveIngestProgressPercent({ percent });
  const ariaLabel =
    resolvedPercent != null && label
      ? `${label} — ${ingestProgressPercentLabel(resolvedPercent)}`
      : label;

  return (
    <div
      className="mdc-workspace-file-card__progress"
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={ariaLabel}
    >
      {resolvedPercent != null ? (
        <progress
          className="mdc-workspace-file-card__progress-bar"
          max={100}
          value={resolvedPercent}
          aria-valuenow={resolvedPercent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      ) : (
        <div
          className="mdc-workspace-file-card__progress-bar mdc-workspace-file-card__progress-bar--indeterminate"
          role="progressbar"
          aria-valuetext={label}
        />
      )}
    </div>
  );
}

function FileCardSubtitle({
  subtitleLabel,
  kindLabel,
  secondaryLabel,
  variant,
}: {
  subtitleLabel?: string;
  kindLabel?: string;
  secondaryLabel?: string;
  variant: WorkspaceFileCardVariant;
}) {
  if (variant === "card" || variant === "chip") {
    const text = subtitleLabel || kindLabel;

    if (!text) {
      return null;
    }

    return <span className="mdc-workspace-file-card__subtitle">{text}</span>;
  }

  if (variant === "row") {
    const text = kindLabel || secondaryLabel;

    if (!text) {
      return null;
    }

    return <span className="mdc-workspace-file-card__subtitle">{text}</span>;
  }

  return null;
}

function FileCardActionButtons({
  filename,
  showInlineActions,
  editable,
  dismissRemove,
  onDownload,
  onRemove,
}: Pick<
  WorkspaceFileCardProps,
  | "filename"
  | "showInlineActions"
  | "editable"
  | "dismissRemove"
  | "onDownload"
  | "onRemove"
>) {
  const hasSideActions =
    (showInlineActions && onDownload) || (editable && onRemove);

  if (!hasSideActions) {
    return null;
  }

  return (
    <div className="mdc-workspace-file-card__actions">
      {showInlineActions && onDownload ? (
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
          className={`mdc-workspace-file-card__action ${dismissRemove ? "" : "mdc-workspace-file-card__action--danger"}`}
          onClick={onRemove}
          aria-label={`Remover ${filename}`}
          title="Remover arquivo"
        >
          {dismissRemove ? (
            <X size={14} aria-hidden="true" />
          ) : (
            <Trash2 size={14} aria-hidden="true" />
          )}
        </button>
      ) : null}
    </div>
  );
}

export function WorkspaceFileCard({
  variant = "card",
  filename,
  kindLabel,
  subtitleLabel,
  sizeLabel,
  statusLabel,
  statusTone = "default",
  iconTone = "brand",
  thumb,
  previewKind = "file",
  editable = false,
  showInlineActions = true,
  dismissRemove = false,
  ingestProgress,
  onPreview,
  onDownload,
  onRemove,
  secondaryLabel,
}: WorkspaceFileCardProps) {
  const previewAriaLabel = `Pré-visualizar ${filename}`;

  const showStructuredDetails =
    Boolean(sizeLabel || statusLabel) ||
    (variant === "row" && Boolean(secondaryLabel && kindLabel));

  const meta = (
    <div className="mdc-workspace-file-card__meta">
      <strong title={filename}>{filename}</strong>
      {showStructuredDetails ? (
        <FileCardDetails
          sizeLabel={sizeLabel}
          statusLabel={statusLabel}
          statusTone={statusTone}
          secondaryLabel={variant === "row" && kindLabel ? secondaryLabel : undefined}
        />
      ) : (
        <FileCardSubtitle
          subtitleLabel={subtitleLabel}
          kindLabel={kindLabel}
          secondaryLabel={secondaryLabel}
          variant={variant}
        />
      )}
    </div>
  );

  const actionButtons = (
    <FileCardActionButtons
      filename={filename}
      showInlineActions={showInlineActions}
      editable={editable}
      dismissRemove={dismissRemove}
      onDownload={onDownload}
      onRemove={onRemove}
    />
  );

  const showIngestProgress = ingestProgress?.active === true;

  const lead = (
    <div className="mdc-workspace-file-card__lead">
      <FileCardIcon
        previewKind={previewKind}
        thumb={thumb}
        iconTone={iconTone}
        compact={variant === "row"}
      />
      {meta}
    </div>
  );

  const hitContent = (
    <>
      {lead}
      {showIngestProgress ? (
        <FileCardIngestProgress
          percent={ingestProgress?.percent}
          label={ingestProgress?.label}
        />
      ) : null}
    </>
  );

  if (variant === "chip") {
    return (
      <span className="mdc-workspace-file-card mdc-workspace-file-card--chip">
        <FileCardIcon previewKind={previewKind} iconTone={iconTone} compact thumb={thumb} />
        <strong title={filename}>{filename}</strong>
        <FileCardSubtitle
          subtitleLabel={subtitleLabel}
          kindLabel={kindLabel}
          variant={variant}
        />
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

  const surfaceClassName =
    variant === "row"
      ? "mdc-workspace-file-card__surface mdc-workspace-file-card__surface--row"
      : "mdc-workspace-file-card__surface";

  const articleClassName =
    variant === "row"
      ? "mdc-workspace-file-card mdc-workspace-file-card--row"
      : "mdc-workspace-file-card mdc-workspace-file-card--card";

  return (
    <article className={articleClassName}>
      <div className={surfaceClassName}>
        {onPreview ? (
          <button
            type="button"
            className="mdc-workspace-file-card__hit mdc-workspace-file-card__hit--interactive"
            onClick={onPreview}
            aria-label={previewAriaLabel}
          >
            {hitContent}
          </button>
        ) : (
          <div className="mdc-workspace-file-card__hit">{hitContent}</div>
        )}
        {actionButtons}
      </div>
    </article>
  );
}
